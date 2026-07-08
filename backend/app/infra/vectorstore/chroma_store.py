import chromadb

from app.core.config import settings
from app.domain.interfaces import VectorStore

_COLLECTION_NAME = "studymate_documents"


class ChromaVectorStore(VectorStore):
    """
    Talks to the ChromaDB server over HTTP (the `chroma` service in docker-compose).
    One shared collection for all documents; per-document isolation is done via
    metadata filtering (`where={"document_id": ...}`), not separate collections --
    keeps this simple while still scaling to many documents/users.
    """

    def __init__(self):
        self.client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
        self.collection = self.client.get_or_create_collection(name=_COLLECTION_NAME)

    def add(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
        documents: list[str],
    ) -> None:
        self.collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)

    def query(self, embedding: list[float], top_k: int, where: dict | None = None) -> list[dict]:
        result = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=where,
        )
        hits = []
        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        for i in range(len(ids)):
            hits.append({
                "id": ids[i],
                "text": docs[i],
                "metadata": metas[i],
                "distance": distances[i],
            })
        return hits

    def delete(self, ids: list[str]) -> None:
        self.collection.delete(ids=ids)
