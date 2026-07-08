import uuid
from sqlalchemy.orm import Session

from app.models.subject import Subject


class SubjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, name: str, owner_id: uuid.UUID) -> Subject:
        subject = Subject(name=name, owner_id=owner_id)
        self.db.add(subject)
        self.db.commit()
        self.db.refresh(subject)
        return subject

    def list_for_user(self, owner_id: uuid.UUID) -> list[Subject]:
        return self.db.query(Subject).filter(Subject.owner_id == owner_id).order_by(Subject.created_at.desc()).all()

    def get_owned(self, subject_id: uuid.UUID, owner_id: uuid.UUID) -> Subject | None:
        return (
            self.db.query(Subject)
            .filter(Subject.id == subject_id, Subject.owner_id == owner_id)
            .first()
        )
