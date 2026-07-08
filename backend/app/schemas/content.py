import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class SummaryRequest(BaseModel):
    mode: Literal["bullets", "paragraphs"] = "bullets"


class SummaryOut(BaseModel):
    document_id: uuid.UUID
    summary: str


class FlashcardGenerateRequest(BaseModel):
    count: int = 10


class FlashcardOut(BaseModel):
    id: uuid.UUID
    question: str
    answer: str
    created_at: datetime

    model_config = {"from_attributes": True}


class QuizGenerateRequest(BaseModel):
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    count: int = 5


class QuizQuestion(BaseModel):
    question: str
    type: Literal["mcq", "true_false", "short_answer"]
    options: list[str] | None = None
    correct_answer: str
    explanation: str | None = None


class QuizOut(BaseModel):
    id: uuid.UUID
    title: str
    difficulty: str
    questions: list[dict]
    created_at: datetime

    model_config = {"from_attributes": True}


class QuizAttemptRequest(BaseModel):
    answers: dict[str, str]  # question index (as string) -> chosen answer


class QuizAttemptOut(BaseModel):
    id: uuid.UUID
    score: int
    total: int
    created_at: datetime

    model_config = {"from_attributes": True}
