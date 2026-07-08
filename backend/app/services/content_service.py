import json
import re
import uuid

from sqlalchemy.orm import Session

from app.domain.interfaces import LLMProvider
from app.repositories.embedding_repository import EmbeddingRepository

MAX_CONTEXT_WORDS = 2500  # keeps prompt + context comfortably inside the local model's context window


def get_document_text(db: Session, document_id: uuid.UUID, max_words: int = MAX_CONTEXT_WORDS) -> str:
    """
    Reassembles the document from its stored chunks (already extracted/chunked
    during ingestion) rather than re-reading the PDF -- reuses Module 2's work.
    Truncated to keep the prompt within the local model's context window.
    """
    chunks = EmbeddingRepository(db).list_for_document(document_id)
    full_text = "\n\n".join(c.chunk_text for c in chunks)
    words = full_text.split()
    if len(words) > max_words:
        words = words[:max_words]
    return " ".join(words)


def extract_json(raw: str):
    """
    LLMs frequently wrap JSON in markdown code fences or add commentary before/after.
    This strips fences and grabs the outermost {...} or [...] block, then parses it.
    Raises ValueError if nothing parseable is found -- callers should treat that as
    a generation failure and can retry or surface a clean error.
    """
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    first_obj = text.find("{")
    first_arr = text.find("[")
    candidates = [i for i in (first_obj, first_arr) if i != -1]
    if not candidates:
        raise ValueError(f"No JSON found in model output: {raw[:200]}")
    start = min(candidates)

    last_obj = text.rfind("}")
    last_arr = text.rfind("]")
    end = max(last_obj, last_arr)
    if end == -1 or end < start:
        raise ValueError(f"No closing JSON bracket found in model output: {raw[:200]}")

    return json.loads(text[start : end + 1])


SUMMARY_SYSTEM = "You are StudyMate AI, a study assistant. Summarize clearly for a student studying for an exam."

FLASHCARD_SYSTEM = """You generate flashcards from lecture material. Respond with ONLY a JSON array, \
no commentary, no markdown fences. Format: [{"question": "...", "answer": "..."}, ...]"""

QUIZ_SYSTEM = """You generate quiz questions from lecture material. Respond with ONLY a JSON array, \
no commentary, no markdown fences. Each item: {"question": "...", "type": "mcq"|"true_false"|"short_answer", \
"options": ["..."] (only for mcq, omit otherwise), "correct_answer": "...", "explanation": "..."}"""


class ContentService:
    def __init__(self, db: Session, llm_provider: LLMProvider):
        self.db = db
        self.llm_provider = llm_provider

    async def generate_summary(self, document_id: uuid.UUID, mode: str = "bullets") -> str:
        text = get_document_text(self.db, document_id)
        if mode == "bullets":
            instruction = "Summarize the following lecture material as clear, concise bullet points covering the key concepts."
        else:
            instruction = "Summarize the following lecture material in a few well-organized paragraphs."

        prompt = f"{instruction}\n\nLecture material:\n{text}\n\nSummary:"
        return await self.llm_provider.generate(prompt, system_prompt=SUMMARY_SYSTEM)

    async def generate_flashcards(self, document_id: uuid.UUID, count: int = 10) -> list[dict]:
        text = get_document_text(self.db, document_id)
        prompt = (
            f"Create exactly {count} flashcards (question + answer pairs) covering the key concepts "
            f"in this lecture material. Keep answers concise (1-2 sentences).\n\n"
            f"Lecture material:\n{text}\n\nJSON array:"
        )
        raw = await self.llm_provider.generate(prompt, system_prompt=FLASHCARD_SYSTEM)
        cards = extract_json(raw)
        if not isinstance(cards, list):
            raise ValueError("Expected a JSON array of flashcards")
        return [{"question": c["question"], "answer": c["answer"]} for c in cards if "question" in c and "answer" in c]

    async def generate_quiz(self, document_id: uuid.UUID, difficulty: str, count: int = 5) -> list[dict]:
        text = get_document_text(self.db, document_id)
        prompt = (
            f"Create exactly {count} {difficulty}-difficulty quiz questions (a mix of multiple choice, "
            f"true/false, and short answer) covering the key concepts in this lecture material.\n\n"
            f"Lecture material:\n{text}\n\nJSON array:"
        )
        raw = await self.llm_provider.generate(prompt, system_prompt=QUIZ_SYSTEM)
        questions = extract_json(raw)
        if not isinstance(questions, list):
            raise ValueError("Expected a JSON array of quiz questions")
        return questions
