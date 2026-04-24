"""
Sage Memory -- Abstract base interface.

All memory backends must implement this contract.
Swap Chroma for Qdrant (or anything else) without touching assistant logic.
"""
from abc import ABC, abstractmethod


class MemoryStore(ABC):

    @abstractmethod
    async def add(self, text: str, metadata: dict) -> None:
        """Store a text chunk with associated metadata."""
        ...

    @abstractmethod
    async def query(self, query: str, k: int = 5) -> list[dict]:
        """
        Retrieve the k most relevant chunks for a query.
        Returns list of dicts: [{"text": ..., "metadata": ..., "score": ...}]
        """
        ...

    @abstractmethod
    async def delete(self, doc_id: str) -> None:
        """Delete a stored chunk by ID."""
        ...

    async def health(self) -> bool:
        """Optional: return True if the backend is reachable."""
        return True
