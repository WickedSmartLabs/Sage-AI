# Sage AI

> *"Polite. Efficient. Occasionally judgmental."*

Sage is a unified personal intelligence layer — a voice-first AI assistant that operates across market systems, infrastructure, documents, and home automation. It is not a chatbot wrapper. It is a system with an assistant interface.

---

## Table of Contents

- [What Sage Is](#what-sage-is)
- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Core Design Principles](#core-design-principles)
- [Layer Breakdown](#layer-breakdown)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Running Sage](#running-sage)
- [API Reference](#api-reference)
- [Adding a New Tool](#adding-a-new-tool)
- [Switching Memory Backends](#switching-memory-backends)
- [Build Phases](#build-phases)
- [Testing](#testing)
- [Roadmap](#roadmap)

---

## What Sage Is

Sage is designed to be a single intelligent operator across multiple domains:

| Domain | Capability |
|---|---|
| Market intelligence | Queries a custom market scanner, interprets signals, references history |
| Systems operation | Docker status, server health, container logs, anomaly detection |
| Document intelligence | RAG over PDFs, books, notes, and config files |
| Home automation | Home Assistant integration, device control with confirmation gates |
| Voice interface | Whisper STT + ElevenLabs TTS, always-on wake word support |

The key distinction: **Sage does not generate answers from model knowledge when real data is available.** Tool output takes priority over the model. Scanner output takes priority over market guesses. Retrieved documents take priority over generic knowledge. The model interprets — it does not invent.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Interface Layer                      │
│         Voice (Whisper / ElevenLabs)  ·  REST API        │
│                  Streamlit UI (planned)                  │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                    Assistant Layer                       │
│   sage/core/assistant.py                                 │
│                                                          │
│   1. Intent classification  (_classify_intent)           │
│   2. Tool orchestration     (router.route)               │
│   3. Context injection      (system message)             │
│   4. Response generation    (OpenAI GPT)                 │
│   5. Logging                (log_interaction)            │
└──────────┬───────────────────────────┬───────────────────┘
           │                           │
┌──────────▼──────────┐   ┌────────────▼──────────────────┐
│    Tool Router       │   │       Memory System           │
│  sage/tools/         │   │  sage/memory/                 │
│                      │   │                               │
│  router.py           │   │  base.py      (interface)     │
│  Pure execution.     │   │  chroma.py    (Phase 1-4)     │
│  No decisions.       │   │  qdrant.py    (Phase 5+)      │
│                      │   │  manager.py   (switcher)      │
│  registry.py         │   │  conversation.py              │
│  scanner.py          │   │                               │
└──────────┬───────────┘   └───────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────────┐
│                   Integration Layer                      │
│                                                          │
│   Market Scanner   Docker   Home Assistant   Filesystem  │
└─────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
sage-ai/
│
├── config/
│   ├── settings.py             # Pydantic settings — all config from .env
│   └── prompts.py              # System prompt and personality strings
│
├── sage/
│   ├── api/
│   │   └── routes.py           # FastAPI routes — thin layer only
│   │
│   ├── core/
│   │   └── assistant.py        # Intent classification + chat orchestration
│   │
│   ├── tools/
│   │   ├── router.py           # Pure execution layer
│   │   ├── registry.py         # Tool registry + OpenAI schemas
│   │   └── scanner.py          # Market Scanner adapter
│   │
│   ├── memory/
│   │   ├── base.py             # Abstract MemoryStore interface
│   │   ├── chroma.py           # ChromaDB implementation
│   │   ├── qdrant.py           # Qdrant implementation (Phase 5+)
│   │   ├── manager.py          # Backend switcher via SAGE_MEMORY_BACKEND
│   │   └── conversation.py     # In-process session memory
│   │
│   ├── retrieval/              # Document RAG pipeline (Phase 6)
│   ├── voice/                  # Whisper + ElevenLabs (Phase 8)
│   └── utils/
│       └── logger.py           # Structured JSONL interaction + tool logger
│
├── tests/
│   ├── unit/
│   │   ├── test_scanner.py
│   │   └── test_conversation.py
│   └── integration/
│       └── golden_prompts.py   # End-to-end eval runner
│
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.dev.yml  # Laptop development stack
│   └── docker-compose.prod.yml # Server production stack
│
├── logs/                       # JSONL logs — gitignored, persisted via volume
├── data/                       # Vector DB storage — gitignored
├── main.py                     # Entry point
├── requirements.txt
├── pyproject.toml
└── .env.example
```

---

## Core Design Principles

### 1. The system controls the brain — not the other way around

The LLM classifies intent and generates language. It does not decide system behavior. Tool execution is deterministic. The router receives a resolved tool name and executes it — it does not ask the model what to do.

### 2. Strict data priority

When generating a response, Sage follows this hierarchy:

```
1. Tool output
2. Scanner data
3. Retrieved documents
4. Conversation memory
5. General model knowledge
```

Model knowledge is the fallback of last resort. If a tool returned data, that data is injected as a system message and the model is explicitly instructed to prioritize it.

### 3. Separation of concerns

Every layer has one job:

| Layer | Responsibility |
|---|---|
| `routes.py` | HTTP surface only — no logic |
| `assistant.py` | Orchestration — classify, route, inject, generate, log |
| `router.py` | Execute a named tool with given args — nothing else |
| `registry.py` | Map tool names to functions and OpenAI schemas |
| `scanner.py` | Speak to the scanner API — nothing else |
| `manager.py` | Return the correct memory backend — nothing else |

### 4. Portable by design

No hardcoded paths. No machine-specific assumptions. All config flows through `.env`. Laptop development and server deployment use identical application code — only the Docker compose files and environment variables differ.

### 5. Observable from day one

Every interaction is logged as structured JSONL before any other feature is added. Logging is not a Phase 4 concern — it is a Phase 0 concern. You cannot improve what you cannot measure.

---

## Layer Breakdown

### Assistant Layer

**`sage/core/assistant.py`**

The orchestration core. Handles the full request lifecycle in five steps:

```
1. _classify_intent()   — asks OpenAI function calling which tool (if any) to invoke
2. router.route()       — executes the resolved tool deterministically
3. context injection    — appends tool result as a system message
4. chat completion      — generates the final response with full context
5. log_interaction()    — writes structured record to interactions.jsonl
```

Intent classification is treated as advisory. If it fails — network error, rate limit, bad response — Sage falls back to a plain assistant response rather than throwing a 500. Classification failure is never surfaced to the user.

The `tool_success` field uses tri-state semantics:

| Value | Meaning |
|---|---|
| `None` | No tool was invoked |
| `True` | Tool ran and succeeded |
| `False` | Tool ran and failed |

This distinction matters for evaluation. "No tool" and "tool failed" are different states and should never be conflated.

### Tool Router

**`sage/tools/router.py`**

A pure execution layer. Accepts a tool name and args. Returns a standardized result. Makes no decisions.

```python
await router.route("scanner_latest", {})

# Returns:
{
    "success": True,
    "tool": "scanner_latest",
    "data": "Signal: bearish_continuation\nDirection: short\n...",
    "error": None
}
```

Handles both async and sync tool functions via `inspect.iscoroutinefunction`. Catches `TypeError` separately from general exceptions so bad argument errors are immediately identifiable. Every execution is logged to `tool_calls.jsonl` with latency.

### Tool Registry

**`sage/tools/registry.py`**

Two responsibilities: maps tool names to handler functions, and provides OpenAI function schemas for intent classification. Adding a new tool requires changes to this file only — the router and classifier pick it up automatically.

### Memory System

**`sage/memory/`**

Built around an abstract interface so the backend is swappable without touching application logic.

```python
class MemoryStore(ABC):
    async def add(self, text: str, metadata: dict) -> None: ...
    async def query(self, query: str, k: int = 5) -> list[dict]: ...
    async def delete(self, doc_id: str) -> None: ...
    async def health(self) -> bool: ...
```

Three named collections, intentionally separate — never mix them:

| Collection | Purpose |
|---|---|
| `sage_memory` | Conversational context |
| `documents` | Document RAG corpus (Phase 6) |
| `scanner` | Market scanner historical data (Phase 5) |

### Logging and Evaluation

**`sage/utils/logger.py`**

Two JSONL log files written from the first request:

**`logs/interactions.jsonl`** — one record per user turn:
```json
{
  "timestamp": "2025-01-01T12:00:00Z",
  "session_id": "dev",
  "user_message": "Sage, what is the market doing?",
  "tool_used": "scanner_latest",
  "tool_success": true,
  "assistant_response": "The scanner indicates bearish continuation, sir.",
  "latency_ms": 1340
}
```

**`logs/tool_calls.jsonl`** — one record per tool execution:
```json
{
  "timestamp": "2025-01-01T12:00:00Z",
  "tool": "scanner_latest",
  "inputs": {},
  "output": "Signal: bearish_continuation\nDirection: short...",
  "success": true,
  "latency_ms": 210
}
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- Docker and Docker Compose (optional but recommended)
- OpenAI API key
- Market scanner running at a known URL (for Phase 3)

### Installation

```bash
git clone https://github.com/WickedSmartLabs/Sage-AI.git
cd Sage-AI

cp .env.example .env
# Edit .env — set OPENAI_API_KEY at minimum

pip install -r requirements.txt
```

---

## Configuration

All configuration is via `.env`. Nothing is hardcoded.

```env
# Mode
SAGE_ENV=development
SAGE_LOG_LEVEL=INFO

# LLM
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# Voice (Phase 8)
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=

# Memory
SAGE_MEMORY_BACKEND=chroma        # chroma | qdrant
CHROMA_HOST=localhost
CHROMA_PORT=8001
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Market Scanner
SCANNER_BASE_URL=http://localhost:9000
SCANNER_API_KEY=

# Server ops (Phase 7)
DOCKER_HOST=unix:///var/run/docker.sock

# Home Assistant (Phase 10)
HA_BASE_URL=http://homeassistant.local:8123
HA_TOKEN=

# API
SAGE_HOST=0.0.0.0
SAGE_PORT=8000
```

---

## Running Sage

### Without Docker

```bash
uvicorn main:app --reload
```

### With Docker (development)

```bash
docker compose -f docker/docker-compose.dev.yml up -d
```

### With Docker (production)

```bash
docker compose -f docker/docker-compose.prod.yml up -d
```

API: `http://localhost:8000`
Docs: `http://localhost:8000/docs`

---

## API Reference

### `POST /api/v1/chat`

```json
// Request
{ "message": "Sage, what is the market doing?", "session_id": "dev" }

// Response
{
  "response": "The scanner indicates bearish continuation with moderate confidence, sir. Structure shows lower highs — I would wait for confirmation before acting.",
  "tool_used": "scanner_latest",
  "latency_ms": 1340,
  "session_id": "dev"
}
```

### `DELETE /api/v1/session/{session_id}`

Clear conversation history for a session.

### `GET /api/v1/health`

```json
{ "status": "ok", "sage": "online" }
```

### `GET /api/v1/memory/health`

```json
{ "backend": "chroma", "reachable": true, "status": "ok" }
```

---

## Adding a New Tool

**1.** Write the handler in `sage/tools/your_tool.py`

**2.** Register it in `sage/tools/registry.py`:

```python
from sage.tools.your_tool import your_handler

TOOL_REGISTRY = {
    "scanner_latest": get_scanner_latest,
    "your_new_tool": your_handler,       # add here
}
```

**3.** Add the OpenAI schema in `get_tool_schemas()`:

```python
{
    "type": "function",
    "function": {
        "name": "your_new_tool",
        "description": "What this tool does and when to call it.",
        "parameters": { "type": "object", "properties": {}, "required": [] },
    },
}
```

**4.** Add golden prompts in `tests/integration/golden_prompts.py`.

The router and classifier pick it up automatically. Nothing else changes.

---

## Switching Memory Backends

To migrate from ChromaDB to Qdrant:

1. Uncomment `qdrant-client>=1.9.0` in `requirements.txt`
2. Run `pip install qdrant-client`
3. Ensure Qdrant is running (included in `docker-compose.prod.yml`)
4. Set `SAGE_MEMORY_BACKEND=qdrant` in `.env`
5. Restart Sage

Application code does not change.

---

## Build Phases

| Phase | Goal | Status |
|---|---|---|
| 0 | Architecture locked — portable, modular, container-ready | Done |
| 1 | Assistant shell — FastAPI, personality, conversation memory | Done |
| 2 | Tool router — deterministic execution layer, registry, logging | Done |
| 3 | Market Scanner integration — flagship interaction end-to-end | Adjust `_format_signal()`, set `SCANNER_BASE_URL` |
| 4 | Eval infrastructure — golden prompts, log queries, latency baselines | Done (logging live from Phase 1) |
| 5 | Memory separation — Qdrant migration, named collections, retrieval policy | Ready to activate |
| 6 | Document RAG — ingestion pipeline, chunking by type, hybrid retrieval | Planned |
| 7 | Server ops tools — Docker status, logs, health summaries | Planned |
| 8 | Voice — Whisper STT, ElevenLabs TTS, streaming response path | Planned |
| 9 | Server migration — deployment-only change, no application rewrite | Planned |
| 10 | Home Assistant — device queries, control with confirmation gates | Planned |

---

## Testing

### Unit tests

```bash
pytest tests/unit/
```

No live API or scanner required. Covers scanner adapter formatting, HTTP error handling, and conversation memory isolation.

### Integration eval

```bash
python tests/integration/golden_prompts.py
```

Runs the golden prompt set against the live API. Checks tool routing accuracy, required and forbidden phrases, and latency. Writes full results to `logs/eval_YYYYMMDD_HHMMSS.jsonl`.

```
Sage Golden Prompt Eval -- 2025-01-01T12:00:00Z
Running 7 prompts against http://localhost:8000/api/v1

------------------------------------------------------------
[PASS] scanner_latest_001 | tool=scanner_latest | 1340ms
       Sage: "The scanner indicates bearish continuation, sir..."

[PASS] no_tool_001 | tool=none | 820ms
       Sage: "Present and accounted for, sir..."

[FAIL] scanner_history_001 | tool=none | 910ms
       -> Expected tool 'scanner_history', got 'None'
------------------------------------------------------------
Results: 6/7 passed
```

---

## Roadmap

**Near term:**
- Complete scanner integration — adjust `_format_signal()` to match live schema
- Run golden prompt eval against live scanner, establish latency baseline
- Begin logging scanner signals to `get_memory("scanner")` collection

**Medium term:**
- Qdrant migration with hybrid BM25 + dense retrieval
- Document ingestion pipeline with chunking strategy per document type
- Docker status and log query tools

**Longer term:**
- Voice interface as a thin layer over the existing text pipeline
- Server migration — environment change only, no code rewrite
- Home Assistant integration with tiered confirmation (lights = low risk, locks = high risk)

---

## Personality Reference

| Situation | Example |
|---|---|
| Acknowledgement | "As you wish, sir." |
| Seeking confirmation | "Shall I proceed, sir?" |
| Tool data received | "The scanner indicates bearish continuation with moderate confidence, sir." |
| Tool failure | "I'm afraid the scanner isn't responding at the moment, sir." |
| Uncertainty | "I don't have reliable data on that at present, sir." |
| Mild sarcasm | "Would you like me to pretend to be impressed, sir?" |

Sage never fabricates tool output. If the data is not there, it says so — in character.
