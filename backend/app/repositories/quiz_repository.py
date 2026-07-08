import uuid
from sqlalchemy.orm import Session

from app.models.quiz import Quiz, QuizAttempt, QuizDifficulty


class QuizRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, document_id: uuid.UUID, difficulty: QuizDifficulty, questions: list[dict], title: str = "Practice Quiz") -> Quiz:
        quiz = Quiz(document_id=document_id, difficulty=difficulty, questions=questions, title=title)
        self.db.add(quiz)
        self.db.commit()
        self.db.refresh(quiz)
        return quiz

    def get(self, quiz_id: uuid.UUID) -> Quiz | None:
        return self.db.query(Quiz).filter(Quiz.id == quiz_id).first()

    def list_for_document(self, document_id: uuid.UUID) -> list[Quiz]:
        return self.db.query(Quiz).filter(Quiz.document_id == document_id).order_by(Quiz.created_at.desc()).all()

    def record_attempt(self, quiz_id: uuid.UUID, user_id: uuid.UUID, answers: dict, score: int, total: int) -> QuizAttempt:
        attempt = QuizAttempt(quiz_id=quiz_id, user_id=user_id, answers=answers, score=score, total=total)
        self.db.add(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        return attempt
