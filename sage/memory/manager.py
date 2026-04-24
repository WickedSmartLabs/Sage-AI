"""
Sage Memory -- Manager (switching layer).

Returns the correct MemoryStore implementation based on SAGE_MEMORY_BACKEND.
Nothing outside this module needs to know which backend is running.

Usage:
    from sage.memory.manager import get_memory
    store = get_memory()                          # default collection
    store = get_memory(collection="documents")    # named collection
    store = get_memory(collection="scanner")      # separate scanner history

Switch backend: set SAGE_MEMORY_BACKEND=qdrant in .env and restart.
"""
from functools import lru_cache
from config.settings import settings
from sage.memory.base import MemoryStore


# One instance per (backend, collection) pair -- avoid reconnecting on every call
@lru_cache(maxsize=16)
def get_memory(collection: str = "sage_memory") -> MemoryStore:
    """
    Return a MemoryStore instance for the given collection.

    Collections are intentionally separate -- do not query across them.
    Recommended collections:
        "sage_memory"   -- short-term conversational memory (Phase 1)
        "documents"     -- document RAG corpus (Phase 6)
        "scanner"       -- market scanner historical data (Phase 5)
    """
    backend = settings.sage_memory_backend

    if backend == "qdrant":
        from sage.memory.qdrant import QdrantMemory
        return QdrantMemory(collection_name=collection)

    # Default: chroma
    from sage.memory.chroma import ChromaMemory
    return ChromaMemory(collection_name=collection)
