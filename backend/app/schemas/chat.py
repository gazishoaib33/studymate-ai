import uuid
from datetime import datetime
from pydantic import BaseModel

from app.models.message import MessageRole


class ChatCreate(BaseModel):
    document_id: uuid.UUID
    title: str | None = None


class ChatOut(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    title: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    content: str


class MessageOut(BaseModel):
    id: uuid.UUID
    role: MessageRole
    content: str
    citations: list[dict] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
