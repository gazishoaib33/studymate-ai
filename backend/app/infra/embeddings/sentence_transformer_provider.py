from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.domain.interfaces import EmbeddingProvider


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    """
    Loads the model once per process (module-level singleton pattern via __init__
    caching) since loading it repeatedly per-request would be slow. all-MiniLM-L6-v2
    is ~80MB, runs fine on CPU, produces 384-dim vectors.
    """

    _model: SentenceTransformer | None = None

    def __init__(self):
        if SentenceTransformerEmbeddingProvider._model is None:
            SentenceTransformerEmbeddingProvider._model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.model = SentenceTransformerEmbeddingProvider._model

    def embed_text(self, text: str) -> list[float]:
        return self.model.encode(text, normalize_embeddings=True).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, normalize_embeddings=True, batch_size=32).tolist()
