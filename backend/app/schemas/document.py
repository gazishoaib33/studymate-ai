import uuid
from datetime import datetime
from pydantic import BaseModel

from app.models.document import DocumentStatus


class DocumentOut(BaseModel):
    id: uuid.UUID
    subject_id: uuid.UUID
    filename: str
    status: DocumentStatus
    page_count: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
