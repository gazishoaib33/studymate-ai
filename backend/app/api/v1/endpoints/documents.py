import os
import uuid
import shutil

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db, SessionLocal
from app.infra.embeddings.sentence_transformer_provider import SentenceTransformerEmbeddingProvider
from app.infra.vectorstore.chroma_store import ChromaVectorStore
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.repositories.subject_repository import SubjectRepository
from app.schemas.document import DocumentOut
from app.services.ingestion_service import IngestionService

router = APIRouter()


def _run_ingestion_in_background(document_id: uuid.UUID) -> None:
    """
    Runs in a background thread after the response is sent. Opens its own DB
    session since the request-scoped one will already be closed by then.
    """
    db = SessionLocal()
    try:
        service = IngestionService(
            db=db,
            embedding_provider=SentenceTransformerEmbeddingProvider(),
            vector_store=ChromaVectorStore(),
        )
        service.process_document(document_id)
    finally:
        db.close()


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def upload_document(
    background_tasks: BackgroundTasks,
    subject_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are supported")

    subject_uuid = uuid.UUID(subject_id)
    subject = SubjectRepository(db).get_owned(subject_uuid, current_user.id)
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    subject_dir = os.path.join(settings.UPLOAD_DIR, str(subject_uuid))
    os.makedirs(subject_dir, exist_ok=True)

    stored_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(subject_dir, stored_filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    document = DocumentRepository(db).create(
        subject_id=subject_uuid,
        filename=file.filename,
        file_path=file_path,
    )

    background_tasks.add_task(_run_ingestion_in_background, document.id)

    return document


@router.get("/", response_model=list[DocumentOut])
def list_documents(
    subject_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    subject_uuid = uuid.UUID(subject_id)
    subject = SubjectRepository(db).get_owned(subject_uuid, current_user.id)
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    return DocumentRepository(db).list_for_subject(subject_uuid)


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = DocumentRepository(db).get(uuid.UUID(document_id))
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Ownership check via the parent subject
    subject = SubjectRepository(db).get_owned(document.subject_id, current_user.id)
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return document
