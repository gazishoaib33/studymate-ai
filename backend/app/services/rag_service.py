import uuid
from typing import AsyncIterator

from app.domain.interfaces import EmbeddingProvider, LLMProvider, VectorStore

TOP_K = 5

SYSTEM_PROMPT = """You are StudyMate AI, a helpful study assistant. Answer the student's \
question using ONLY the provided lecture excerpts below. If the excerpts don't contain \
enough information to answer, say so honestly instead of guessing. Keep answers clear \
and student-friendly. Do not mention "excerpts" or "context" explicitly in your answer -- \
just answer naturally as a tutor would."""


def build_prompt(question: str, chunks: list[dict]) -> str:
    context_block = "\n\n".join(
        f"[Source {i + 1}, page {c['metadata'].get('page_number', '?')}]\n{c['text']}"
        for i, c in enumerate(chunks)
    )
    return f"""Lecture excerpts:
{context_block}

Student's question: {question}

Answer:"""


class RAGService:
    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        llm_provider: LLMProvider,
    ):
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.llm_provider = llm_provider

    def retrieve(self, question: str, document_id: uuid.UUID, top_k: int = TOP_K) -> list[dict]:
        query_embedding = self.embedding_provider.embed_text(question)
        return self.vector_store.query(
            embedding=query_embedding,
            top_k=top_k,
            where={"document_id": str(document_id)},
        )

    @staticmethod
    def to_citations(chunks: list[dict]) -> list[dict]:
        return [
            {
                "chunk_id": c["id"],
                "page": c["metadata"].get("page_number"),
                "text_preview": c["text"][:200],
            }
            for c in chunks
        ]

    async def answer_stream(self, question: str, document_id: uuid.UUID) -> tuple[AsyncIterator[str], list[dict]]:
        """Returns (token_stream, citations). Citations are known upfront since
        retrieval happens before generation starts."""
        chunks = self.retrieve(question, document_id)
        prompt = build_prompt(question, chunks)
        citations = self.to_citations(chunks)
        token_stream = self.llm_provider.stream(prompt, system_prompt=SYSTEM_PROMPT)
        return token_stream, citations
