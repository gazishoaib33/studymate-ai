import uuid
from sqlalchemy.orm import Session

from app.models.chat import Chat


class ChatRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, owner_id: uuid.UUID, document_id: uuid.UUID, title: str | None = None) -> Chat:
        chat = Chat(owner_id=owner_id, document_id=document_id, title=title or "New chat")
        self.db.add(chat)
        self.db.commit()
        self.db.refresh(chat)
        return chat

    def get_owned(self, chat_id: uuid.UUID, owner_id: uuid.UUID) -> Chat | None:
        return self.db.query(Chat).filter(Chat.id == chat_id, Chat.owner_id == owner_id).first()

    def list_for_user(self, owner_id: uuid.UUID) -> list[Chat]:
        return self.db.query(Chat).filter(Chat.owner_id == owner_id).order_by(Chat.created_at.desc()).all()
