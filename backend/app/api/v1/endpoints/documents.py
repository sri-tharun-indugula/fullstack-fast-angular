import uuid

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import FileResponse

from app.api.deps import CurrentUser, SessionDep
from app.models.document import DocumentScope
from app.schemas.document import DocumentPublic
from app.services import documents as documents_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/me", response_model=list[DocumentPublic])
async def my_documents(session: SessionDep, current_user: CurrentUser) -> list[DocumentPublic]:
    return await documents_service.list_visible(session, current_user)


@router.get("/{document_id}/content")
async def download_document(document_id: uuid.UUID, session: SessionDep, current_user: CurrentUser) -> FileResponse:
    doc, path = await documents_service.get_download_path(session, current_user, document_id)
    return FileResponse(
        path,
        media_type=doc.content_type,
        filename=doc.original_filename,
    )


@router.post("", response_model=DocumentPublic, status_code=201)
async def upload_document(
    session: SessionDep,
    current_user: CurrentUser,
    title: str = Form(...),
    scope: DocumentScope = Form(...),
    file: UploadFile = File(...),
    description: str | None = Form(None),
    owner_user_id: uuid.UUID | None = Form(None),
) -> DocumentPublic:
    return await documents_service.upload_document(
        session,
        current_user,
        title=title,
        description=description,
        scope=scope,
        owner_user_id=owner_user_id,
        file=file,
    )


@router.delete("/{document_id}", status_code=204)
async def remove_document(document_id: uuid.UUID, session: SessionDep, current_user: CurrentUser) -> None:
    await documents_service.delete_document(session, current_user, document_id)
