import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.infra.llm.ollama_provider import OllamaProvider
from app.models.document import DocumentStatus
from app.models.quiz import QuizDifficulty
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.repositories.flashcard_repository import FlashcardRepository
from app.repositories.quiz_repository import QuizRepository
from app.repositories.subject_repository import SubjectRepository
from app.schemas.content import (
    FlashcardGenerateRequest,
    FlashcardOut,
    QuizAttemptOut,
    QuizAttemptRequest,
    QuizGenerateRequest,
    QuizOut,
    SummaryOut,
    SummaryRequest,
)
from app.services.content_service import ContentService

router = APIRouter()


def _get_owned_ready_document_or_404(db: Session, document_id: uuid.UUID, user: User):
    document = DocumentRepository(db).get(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    subject = SubjectRepository(db).get_owned(document.subject_id, user.id)
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if document.status != DocumentStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document is not ready yet (status: {document.status.value}).",
        )
    return document


@router.post("/{document_id}/summary", response_model=SummaryOut)
async def generate_summary(
    document_id: str,
    payload: SummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc_uuid = uuid.UUID(document_id)
    document = _get_owned_ready_document_or_404(db, doc_uuid, current_user)

    service = ContentService(db=db, llm_provider=OllamaProvider())
    try:
        summary = await service.generate_summary(doc_uuid, mode=payload.mode)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Summary generation failed: {e}")

    DocumentRepository(db).update_summary(doc_uuid, summary)
    return SummaryOut(document_id=document.id, summary=summary)


@router.get("/{document_id}/summary", response_model=SummaryOut)
def get_cached_summary(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc_uuid = uuid.UUID(document_id)
    document = _get_owned_ready_document_or_404(db, doc_uuid, current_user)
    if not document.summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No summary generated yet")
    return SummaryOut(document_id=document.id, summary=document.summary)


@router.post("/{document_id}/flashcards", response_model=list[FlashcardOut])
async def generate_flashcards(
    document_id: str,
    payload: FlashcardGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc_uuid = uuid.UUID(document_id)
    _get_owned_ready_document_or_404(db, doc_uuid, current_user)

    service = ContentService(db=db, llm_provider=OllamaProvider())
    try:
        cards = await service.generate_flashcards(doc_uuid, count=payload.count)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Flashcard generation failed: {e}")

    if not cards:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Model returned no usable flashcards")

    return FlashcardRepository(db).bulk_create(doc_uuid, cards)


@router.get("/{document_id}/flashcards", response_model=list[FlashcardOut])
def list_flashcards(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc_uuid = uuid.UUID(document_id)
    _get_owned_ready_document_or_404(db, doc_uuid, current_user)
    return FlashcardRepository(db).list_for_document(doc_uuid)


@router.post("/{document_id}/quiz", response_model=QuizOut)
async def generate_quiz(
    document_id: str,
    payload: QuizGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc_uuid = uuid.UUID(document_id)
    _get_owned_ready_document_or_404(db, doc_uuid, current_user)

    service = ContentService(db=db, llm_provider=OllamaProvider())
    try:
        questions = await service.generate_quiz(doc_uuid, difficulty=payload.difficulty, count=payload.count)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Quiz generation failed: {e}")

    if not questions:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Model returned no usable questions")

    return QuizRepository(db).create(
        document_id=doc_uuid,
        difficulty=QuizDifficulty(payload.difficulty),
        questions=questions,
    )


@router.get("/{document_id}/quiz", response_model=list[QuizOut])
def list_quizzes(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc_uuid = uuid.UUID(document_id)
    _get_owned_ready_document_or_404(db, doc_uuid, current_user)
    return QuizRepository(db).list_for_document(doc_uuid)


@router.post("/quiz/{quiz_id}/attempt", response_model=QuizAttemptOut)
def submit_quiz_attempt(
    quiz_id: str,
    payload: QuizAttemptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quiz_repo = QuizRepository(db)
    quiz = quiz_repo.get(uuid.UUID(quiz_id))
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

    # Ownership check via the parent document's subject
    _get_owned_ready_document_or_404(db, quiz.document_id, current_user)

    score = 0
    for idx, question in enumerate(quiz.questions):
        submitted = payload.answers.get(str(idx), "").strip().lower()
        correct = str(question.get("correct_answer", "")).strip().lower()
        if submitted and submitted == correct:
            score += 1

    return quiz_repo.record_attempt(
        quiz_id=quiz.id,
        user_id=current_user.id,
        answers=payload.answers,
        score=score,
        total=len(quiz.questions),
    )
