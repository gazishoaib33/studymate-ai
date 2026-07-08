import uuid
from sqlalchemy.orm import Session

from app.models.flashcard import Flashcard


class FlashcardRepository:
    def __init__(self, db: Session):
        self.db = db

    def bulk_create(self, document_id: uuid.UUID, cards: list[dict]) -> list[Flashcard]:
        objects = [Flashcard(document_id=document_id, question=c["question"], answer=c["answer"]) for c in cards]
        self.db.add_all(objects)
        self.db.commit()
        for obj in objects:
            self.db.refresh(obj)
        return objects

    def list_for_document(self, document_id: uuid.UUID) -> list[Flashcard]:
        return (
            self.db.query(Flashcard)
            .filter(Flashcard.document_id == document_id)
            .order_by(Flashcard.created_at)
            .all()
        )

    def delete_for_document(self, document_id: uuid.UUID) -> None:
        self.db.query(Flashcard).filter(Flashcard.document_id == document_id).delete()
        self.db.commit()
