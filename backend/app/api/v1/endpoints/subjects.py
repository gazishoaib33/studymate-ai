from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.subject_repository import SubjectRepository
from app.schemas.subject import SubjectCreate, SubjectOut

router = APIRouter()


@router.post("/", response_model=SubjectOut, status_code=status.HTTP_201_CREATED)
def create_subject(
    payload: SubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return SubjectRepository(db).create(name=payload.name, owner_id=current_user.id)


@router.get("/", response_model=list[SubjectOut])
def list_subjects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return SubjectRepository(db).list_for_user(current_user.id)


@router.get("/{subject_id}", response_model=SubjectOut)
def get_subject(
    subject_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import uuid as uuid_module

    subject = SubjectRepository(db).get_owned(uuid_module.UUID(subject_id), current_user.id)
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    return subject
