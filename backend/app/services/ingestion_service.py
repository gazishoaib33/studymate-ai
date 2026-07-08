import uuid
import fitz  # PyMuPDF

from sqlalchemy.orm import Session

from app.domain.interfaces import EmbeddingProvider, VectorStore
from app.models.document import DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.repositories.embedding_repository import EmbeddingRepository

CHUNK_SIZE_WORDS = 300
CHUNK_OVERLAP_WORDS = 50


def extract_pages(file_path: str) -> list[tuple[int, str]]:
    """Returns [(page_number, page_text), ...], 1-indexed pages."""
    pages: list[tuple[int, str]] = []
    with fitz.open(file_path) as pdf:
        for i, page in enumerate(pdf, start=1):
            text = page.get_text().strip()
            if text:
                pages.append((i, text))
    return pages


def chunk_pages(pages: list[tuple[int, str]]) -> list[tuple[int, int, str]]:
    """
    Word-based sliding-window chunking with overlap, tracking which page each
    chunk started on. Word-based (not character-based) keeps chunks semantically
    coherent enough for embeddings without needing a tokenizer here.

    Returns [(chunk_index, page_number, chunk_text), ...]
    """
    chunks: list[tuple[int, int, str]] = []
    chunk_index = 0

    for page_number, text in pages:
        words = text.split()
        start = 0
        while start < len(words):
            end = start + CHUNK_SIZE_WORDS
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)
            if chunk_text.strip():
                chunks.append((chunk_index, page_number, chunk_text))
                chunk_index += 1
            if end >= len(words):
                break
            start = end - CHUNK_OVERLAP_WORDS

    return chunks


class IngestionService:
    """
    Orchestrates the full pipeline: PDF -> extracted pages -> chunks -> embeddings
    -> ChromaDB (vectors) + Postgres (chunk metadata). Runs synchronously via a
    FastAPI BackgroundTask for the MVP; swap for a Celery task in Module 5 without
    changing this class's logic, just how it's invoked.
    """

    def __init__(self, db: Session, embedding_provider: EmbeddingProvider, vector_store: VectorStore):
        self.db = db
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.document_repo = DocumentRepository(db)
        self.embedding_repo = EmbeddingRepository(db)

    def process_document(self, document_id: uuid.UUID) -> None:
        document = self.document_repo.get(document_id)
        if not document:
            return

        try:
            self.document_repo.update_status(document_id, DocumentStatus.PROCESSING)

            pages = extract_pages(document.file_path)
            if not pages:
                self.document_repo.update_status(document_id, DocumentStatus.FAILED)
                return

            chunks = chunk_pages(pages)
            chunk_texts = [c[2] for c in chunks]

            embeddings = self.embedding_provider.embed_batch(chunk_texts)

            chroma_ids = [f"{document_id}_{chunk_index}" for chunk_index, _, _ in chunks]
            metadatas = [
                {"document_id": str(document_id), "page_number": page_number, "chunk_index": chunk_index}
                for chunk_index, page_number, _ in chunks
            ]

            self.vector_store.add(
                ids=chroma_ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=chunk_texts,
            )

            embedding_rows = [
                {
                    "document_id": document_id,
                    "chroma_id": chroma_ids[i],
                    "chunk_text": chunks[i][2],
                    "page_number": chunks[i][1],
                    "chunk_index": chunks[i][0],
                }
                for i in range(len(chunks))
            ]
            self.embedding_repo.bulk_create(embedding_rows)

            self.document_repo.update_status(document_id, DocumentStatus.READY, page_count=len(pages))

        except Exception:
            self.document_repo.update_status(document_id, DocumentStatus.FAILED)
            raise
