import uuid
from sqlalchemy.orm import Session

from app.models.message import Message, MessageRole


class MessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        chat_id: uuid.UUID,
        role: MessageRole,
        content: str,
        citations: list[dict] | None = None,
    ) -> Message:
        message = Message(chat_id=chat_id, role=role, content=content, citations=citations)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def list_for_chat(self, chat_id: uuid.UUID) -> list[Message]:
        return self.db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.created_at).all()
