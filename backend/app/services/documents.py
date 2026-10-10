import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.document import DocumentScope, HrDocument
from app.models.employee import EmployeeProfile
from app.models.audit import AuditAction
from app.models.notification import NotificationKind
from app.services import audit as audit_service
from app.models.user import Role, User
from app.schemas.document import DocumentPublic
from app.services import notifications as notifications_service

_ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "text/plain",
    "image/png",
    "image/jpeg",
}


def _storage_root() -> Path:
    root = get_settings().documents_storage_path
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_extension(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix and len(suffix) <= 10 and suffix.replace(".", "").isalnum():
        return suffix
    return ""


def _to_public(doc: HrDocument) -> DocumentPublic:
    return DocumentPublic(
        id=doc.id,
        scope=doc.scope,
        owner_user_id=doc.owner_user_id,
        owner_name=doc.owner.full_name if doc.owner else None,
        uploaded_by_user_id=doc.uploaded_by_user_id,
        uploaded_by_name=doc.uploaded_by.full_name,
        title=doc.title,
        description=doc.description,
        original_filename=doc.original_filename,
        content_type=doc.content_type,
        size_bytes=doc.size_bytes,
        created_at=doc.created_at,
    )


async def _load_document(session: AsyncSession, document_id: uuid.UUID) -> HrDocument | None:
    result = await session.execute(
        select(HrDocument)
        .where(HrDocument.id == document_id)
        .options(selectinload(HrDocument.owner), selectinload(HrDocument.uploaded_by))
    )
    return result.scalar_one_or_none()


async def _require_profile(session: AsyncSession, user: User) -> EmployeeProfile:
    profile = await session.scalar(select(EmployeeProfile).where(EmployeeProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee profile required")
    return profile


async def _can_manage_owner(session: AsyncSession, viewer: User, owner_user_id: uuid.UUID) -> bool:
    if viewer.role == Role.admin:
        return True
    if viewer.id == owner_user_id:
        return True
    if viewer.role == Role.manager:
        profile = await session.scalar(select(EmployeeProfile).where(EmployeeProfile.user_id == owner_user_id))
        return profile is not None and profile.manager_user_id == viewer.id
    return False


def _can_view(viewer: User, doc: HrDocument, viewer_profile: EmployeeProfile | None, owner_profile: EmployeeProfile | None) -> bool:
    if viewer.role == Role.admin:
        return True
    if doc.scope == DocumentScope.company:
        return viewer_profile is not None
    if doc.owner_user_id is None:
        return False
    if doc.owner_user_id == viewer.id:
        return True
    if viewer.role == Role.manager and owner_profile is not None and owner_profile.manager_user_id == viewer.id:
        return True
    return False


async def list_visible(session: AsyncSession, user: User) -> list[DocumentPublic]:
    viewer_profile = await session.scalar(select(EmployeeProfile).where(EmployeeProfile.user_id == user.id))
    visibility: list = []

    if viewer_profile is not None or user.role == Role.admin:
        visibility.append(HrDocument.scope == DocumentScope.company)

    employee_scope = HrDocument.scope == DocumentScope.employee
    if user.role == Role.admin:
        visibility.append(employee_scope)
    elif user.role == Role.manager:
        reports = select(EmployeeProfile.user_id).where(EmployeeProfile.manager_user_id == user.id)
        visibility.append(
            employee_scope
            & or_(HrDocument.owner_user_id == user.id, HrDocument.owner_user_id.in_(reports))
        )
    else:
        visibility.append(employee_scope & (HrDocument.owner_user_id == user.id))

    if not visibility:
        return []

    result = await session.execute(
        select(HrDocument)
        .where(or_(*visibility))
        .options(selectinload(HrDocument.owner), selectinload(HrDocument.uploaded_by))
        .order_by(HrDocument.created_at.desc())
    )
    return [_to_public(item) for item in result.scalars().all()]


async def get_download_path(session: AsyncSession, user: User, document_id: uuid.UUID) -> tuple[HrDocument, Path]:
    doc = await _load_document(session, document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    viewer_profile = await session.scalar(select(EmployeeProfile).where(EmployeeProfile.user_id == user.id))
    owner_profile = None
    if doc.owner_user_id is not None:
        owner_profile = await session.scalar(
            select(EmployeeProfile).where(EmployeeProfile.user_id == doc.owner_user_id)
        )
    if not _can_view(user, doc, viewer_profile, owner_profile):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    path = _storage_root() / doc.stored_filename
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File missing on server")
    return doc, path


async def upload_document(
    session: AsyncSession,
    user: User,
    *,
    title: str,
    description: str | None,
    scope: DocumentScope,
    owner_user_id: uuid.UUID | None,
    file: UploadFile,
) -> DocumentPublic:
    await _require_profile(session, user)

    if scope == DocumentScope.company:
        if user.role != Role.admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can upload company documents")
        owner_user_id = None
    else:
        if owner_user_id is None:
            owner_user_id = user.id
        if not await _can_manage_owner(session, user, owner_user_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        owner_profile = await session.scalar(select(EmployeeProfile).where(EmployeeProfile.user_id == owner_user_id))
        if owner_profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner employee profile not found")

    if file.filename is None or not file.filename.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Filename required")
    content_type = file.content_type or "application/octet-stream"
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="File type not allowed")

    max_bytes = get_settings().document_max_bytes
    data = await file.read()
    if len(data) == 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Empty file")
    if len(data) > max_bytes:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="File too large")

    stored_name = f"{uuid.uuid4().hex}{_safe_extension(file.filename)}"
    path = _storage_root() / stored_name
    path.write_bytes(data)

    doc = HrDocument(
        scope=scope,
        owner_user_id=owner_user_id,
        uploaded_by_user_id=user.id,
        title=title.strip(),
        description=description.strip() if description else None,
        original_filename=Path(file.filename).name[:512],
        stored_filename=stored_name,
        content_type=content_type,
        size_bytes=len(data),
    )
    session.add(doc)
    await session.flush()
    loaded = await _load_document(session, doc.id)
    assert loaded is not None

    if scope == DocumentScope.company:
        profiles = await session.execute(select(EmployeeProfile.user_id))
        for uid in profiles.scalars().all():
            await notifications_service.create_notification(
                session,
                user_id=uid,
                kind=NotificationKind.document_available,
                title="New company document",
                body=loaded.title,
                entity_type="document",
                entity_id=loaded.id,
            )
    elif owner_user_id is not None and owner_user_id != user.id:
        await notifications_service.create_notification(
            session,
            user_id=owner_user_id,
            kind=NotificationKind.document_available,
            title="New document shared with you",
            body=loaded.title,
            entity_type="document",
            entity_id=loaded.id,
        )

    await audit_service.record(
        session,
        action=AuditAction.document_uploaded,
        summary=f'{user.full_name} uploaded document "{loaded.title}"',
        actor_user_id=user.id,
        entity_type="document",
        entity_id=loaded.id,
        metadata={"scope": loaded.scope.value},
    )
    return _to_public(loaded)


async def delete_document(session: AsyncSession, user: User, document_id: uuid.UUID) -> None:
    doc = await _load_document(session, document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if user.role != Role.admin and doc.uploaded_by_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    path = _storage_root() / doc.stored_filename
    doc_id = doc.id
    title = doc.title
    await session.delete(doc)
    await session.flush()
    if path.is_file():
        path.unlink()
    await audit_service.record(
        session,
        action=AuditAction.document_deleted,
        summary=f'{user.full_name} deleted document "{title}"',
        actor_user_id=user.id,
        entity_type="document",
        entity_id=doc_id,
    )
