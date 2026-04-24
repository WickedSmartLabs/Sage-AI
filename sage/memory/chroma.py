"""
Sage Memory -- ChromaDB backend.

Default backend for Phase 1-4. Zero config beyond CHROMA_HOST/PORT in .env.
"""
import uuid
import chromadb
from chromadb.config import Settings as ChromaSettings
from sage.memory.base import MemoryStore
from config.settings import settings


class ChromaMemory(MemoryStore):

    def __init__(self, collection_name: str = "sage_memory"):
        self._collection_name = collection_name
        self._client = None
        self._collection = None

    def _get_collection(self):
        """Lazy init -- only connect when first used."""
        if self._collection is None:
            self._client = chromadb.PersistentClient(
                path=settings.chroma_persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
)
            
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    async def add(self, text: str, metadata: dict) -> None:
        collection = self._get_collection()
        doc_id = metadata.get("id") or str(uuid.uuid4())
        collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id],
        )

    async def query(self, query: str, k: int = 5) -> list[dict]:
        collection = self._get_collection()
        results = collection.query(
            query_texts=[query],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )

        output = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(docs, metas, distances):
            output.append({
                "text": doc,
                "metadata": meta,
                "score": round(1 - dist, 4),  # cosine distance -> similarity
            })
        return output

    async def delete(self, doc_id: str) -> None:
        collection = self._get_collection()
        collection.delete(ids=[doc_id])

    async def health(self) -> bool:
        try:
            self._get_collection()
            return True
        except Exception:
            return False
