# Retrieval -- Phase 5 & 6

This module will contain:
- Document memory (Qdrant -- hybrid dense + sparse retrieval)
- Scanner/system historical memory (structured DB + optional embeddings)

Not active in Phase 1-3. Stub is here to reserve the module boundary.

## When building (Phase 5):

Use separate collections per memory type. Do not mix conversation,
documents, and scanner history into one retrieval pool.

Memory types:
- Conversation: lightweight session storage + summarisation
- Documents: Qdrant with hybrid BM25 + dense embedding retrieval
- Scanner history: structured DB (SQLite/Postgres) + optional embeddings later

## Chunking strategy notes (Phase 6):

Different document types need different chunking logic:
- Books: preserve section/chapter structure, chunk by section header
- PDFs: paragraph-level chunks, 300-500 tokens, 10% overlap
- Notes/markdown: paragraph-level, smaller chunks, high overlap
- Configs: key-value aware chunking, preserve context of parent block

## Retrieval merge policy (define before wiring into assistant.py):

1. Always check conversation memory first (recency-weighted)
2. Check document memory only when user asks about documents or knowledge
3. Check scanner history only for market/signal queries
4. Never mix scanner history into document retrieval results
