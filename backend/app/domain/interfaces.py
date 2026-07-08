"""
Abstract interfaces for the AI layer (Repository-pattern style "ports").

Why this exists: the MVP uses Ollama + Sentence-Transformers + Chroma because
they're free and local. Defining these interfaces now means swapping in
Claude/OpenAI/Gemini later, or a different vector DB, is a matter of writing
one new adapter class in app/infra/ -- not touching services or API code.

Concrete implementations live in app/infra/llm, app/infra/embeddings,
app/infra/vectorstore. Wired to services via simple constructor injection
(no DI framework needed at this scale).
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Non-streaming completion. Used for quiz/flashcard/summary generation."""
        ...

    @abstractmethod
    async def stream(self, prompt: str, system_prompt: str | None = None) -> AsyncIterator[str]:
        """Streaming completion, used for the chat endpoint."""
        ...


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        ...

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        ...


class VectorStore(ABC):
    @abstractmethod
    def add(self, ids: list[str], embeddings: list[list[float]], metadatas: list[dict], documents: list[str]) -> None:
        ...

    @abstractmethod
    def query(self, embedding: list[float], top_k: int, where: dict | None = None) -> list[dict]:
        """Returns a list of {id, text, metadata, distance}."""
        ...

    @abstractmethod
    def delete(self, ids: list[str]) -> None:
        ...
