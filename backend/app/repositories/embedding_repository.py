import uuid
from sqlalchemy.orm import Session

from app.models.embedding import Embedding


class EmbeddingRepository:
    def __init__(self, db: Session):
        self.db = db

    def bulk_create(self, rows: list[dict]) -> None:
        """rows: list of {document_id, chroma_id, chunk_text, page_number, chunk_index}"""
        objects = [Embedding(**row) for row in rows]
        self.db.add_all(objects)
        self.db.commit()

    def list_for_document(self, document_id: uuid.UUID) -> list[Embedding]:
        return (
            self.db.query(Embedding)
            .filter(Embedding.document_id == document_id)
            .order_by(Embedding.chunk_index)
            .all()
        )
