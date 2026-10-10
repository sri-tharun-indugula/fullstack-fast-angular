import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.document import DocumentScope


class DocumentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scope: DocumentScope
    owner_user_id: uuid.UUID | None
    owner_name: str | None
    uploaded_by_user_id: uuid.UUID
    uploaded_by_name: str
    title: str
    description: str | None
    original_filename: str
    content_type: str
    size_bytes: int
    created_at: datetime


class DocumentUploadMeta(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    scope: DocumentScope
    owner_user_id: uuid.UUID | None = None
