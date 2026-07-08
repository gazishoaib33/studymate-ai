import uuid
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, subject_id: uuid.UUID, filename: str, file_path: str) -> Document:
        document = Document(subject_id=subject_id, filename=filename, file_path=file_path)
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def get(self, document_id: uuid.UUID) -> Document | None:
        return self.db.query(Document).filter(Document.id == document_id).first()

    def list_for_subject(self, subject_id: uuid.UUID) -> list[Document]:
        return (
            self.db.query(Document)
            .filter(Document.subject_id == subject_id)
            .order_by(Document.created_at.desc())
            .all()
        )

    def update_status(self, document_id: uuid.UUID, status: DocumentStatus, page_count: int | None = None) -> None:
        document = self.get(document_id)
        if document:
            document.status = status
            if page_count is not None:
                document.page_count = page_count
            self.db.commit()

    def update_summary(self, document_id: uuid.UUID, summary: str) -> None:
        document = self.get(document_id)
        if document:
            document.summary = summary
            self.db.commit()
