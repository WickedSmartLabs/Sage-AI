"""
Sage Memory -- Qdrant backend.

Phase 5+ backend. Supports hybrid search (dense + sparse/BM25).
Uncomment qdrant-client in requirements.txt before using.

Switch via: SAGE_MEMORY_BACKEND=qdrant in .env
"""
import uuid
from sage.memory.base import MemoryStore
from config.settings import settings


class QdrantMemory(MemoryStore):
    """
    Qdrant-backed memory store with hybrid retrieval support.

    Requires:
        pip install qdrant-client openai  (for embeddings)
        Qdrant running at QDRANT_HOST:QDRANT_PORT
    """

    VECTOR_SIZE = 1536  # text-embedding-3-small output size

    def __init__(self, collection_name: str = "sage_memory"):
        self._collection_name = collection_name
        self._client = None
        self._embedder = None

    def _get_client(self):
        if self._client is None:
            from qdrant_client import QdrantClient
            self._client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
            )
            self._ensure_collection()
        return self._client

    def _ensure_collection(self):
        from qdrant_client.models import Distance, VectorParams
        existing = [c.name for c in self._client.get_collections().collections]
        if self._collection_name not in existing:
            self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )

    async def _embed(self, text: str) -> list[float]:
        """Generate embedding using OpenAI text-embedding-3-small."""
        from openai import AsyncOpenAI
        from config.settings import settings as s
        if self._embedder is None:
            self._embedder = AsyncOpenAI(api_key=s.openai_api_key)
        response = await self._embedder.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding

    async def add(self, text: str, metadata: dict) -> None:
        from qdrant_client.models import PointStruct
        client = self._get_client()
        doc_id = metadata.get("id") or str(uuid.uuid4())
        vector = await self._embed(text)
        client.upsert(
            collection_name=self._collection_name,
            points=[
                PointStruct(
                    id=doc_id,
                    vector=vector,
                    payload={**metadata, "text": text},
                )
            ],
        )

    async def query(self, query: str, k: int = 5) -> list[dict]:
        client = self._get_client()
        query_vector = await self._embed(query)
        results = client.search(
            collection_name=self._collection_name,
            query_vector=query_vector,
            limit=k,
            with_payload=True,
        )
        return [
            {
                "text": hit.payload.get("text", ""),
                "metadata": {k: v for k, v in hit.payload.items() if k != "text"},
                "score": round(hit.score, 4),
            }
            for hit in results
        ]

    async def delete(self, doc_id: str) -> None:
        from qdrant_client.models import PointIdsList
        client = self._get_client()
        client.delete(
            collection_name=self._collection_name,
            points_selector=PointIdsList(points=[doc_id]),
        )

    async def health(self) -> bool:
        try:
            self._get_client()
            return True
        except Exception:
            return False
