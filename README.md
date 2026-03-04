# Sage-AI

Sage-AI is a modular AI assistant framework that combines conversational context, rule-based learning, and API-driven interaction through a FastAPI service.

The system explores how conversational assistants can be structured internally using separate components for conversation management, reasoning, and knowledge learning. Instead of acting as a simple chatbot, Sage-AI demonstrates how user input can flow through a processing engine that manages context, retrieves learned information, and generates structured responses.

> ⚠️ **Status:** Active development. Core architecture is implemented while additional capabilities are being expanded.

---

## Problem

Most conversational AI systems operate as simple prompt-response tools with no persistent context or structured reasoning layer. This limits their ability to remember information, adapt to users, or evolve through interaction.

Building more capable AI assistants requires an architecture that separates conversation handling, reasoning logic, and knowledge storage.

---

## Solution

Sage-AI implements a modular assistant architecture that processes conversational input through a centralized AI engine.

The system records conversation history, checks for previously learned knowledge, and generates responses using a structured processing pipeline. This approach allows the assistant to gradually learn new information while maintaining a clear and explainable response process.

---

## System Architecture

Sage-AI follows a service-based architecture where an API layer communicates with a centralized AI processing engine.

```mermaid
flowchart TD
    A[User Request] --> B[FastAPI Service]
    B --> C[AI Engine]
    C --> D[Conversation Manager]
    C --> E[Learning Engine]
    D --> F[Conversation Context]
    E --> G[Learned Knowledge]
    C --> H[Response Generation]
    H --> I[API Response]
```

### Components

| Component | Description |
|---|---|
| **FastAPI Service** | Provides the HTTP interface used to interact with the assistant. |
| **AI Engine** | Coordinates how user input is processed and determines how responses are generated. |
| **Conversation Manager** | Tracks conversation history and manages contextual information. |
| **Learning Engine** | Stores and retrieves knowledge learned during conversations. |

### Processing Workflow

1. A user sends a message to the `/chat` endpoint.
2. The FastAPI service forwards the request to the AI engine.
3. The conversation manager records the message in the conversation history.
4. The learning engine checks for previously learned knowledge related to the prompt.
5. If a match is found, the stored response is returned.
6. Otherwise, the assistant returns a fallback response and invites the user to teach it new information.
7. The response is returned to the API client with a confidence score and source label.

---

## Technology Stack

**Application Layer**
- Python
- FastAPI
- Pydantic

**System Architecture**
- Modular AI processing engine
- Conversation state management
- Rule-based knowledge learning

**Development Tools**
- Uvicorn
- Async Python architecture

---

## Current Features

- FastAPI-based conversational API
- Modular AI processing engine
- Conversation tracking
- Rule-based knowledge learning
- Confidence scoring for responses
- Structured response objects for API clients

---

## Project Structure

```
sage-ai/
├── core/
│   ├── ai_engine.py
│   ├── conversation_manager.py
│   └── learning_engine.py
└── main.py
```

- **`main.py`** — Defines the FastAPI application and API endpoints.
- **`ai_engine.py`** — Central orchestration component that processes user inputs.
- **`conversation_manager.py`** — Maintains conversation context.
- **`learning_engine.py`** — Handles storing and retrieving learned knowledge.

---

## API Usage

Start the API server:

```bash
uvicorn main:app --reload
```

The service will run at `http://localhost:8000`.

### Health Check

```http
GET /
```

**Example response:**

```json
{
  "status": "online",
  "service": "Sage v2"
}
```

### Chat Endpoint

```http
POST /chat
```

**Example request:**

```json
{
  "message": "Hello Sage"
}
```

**Example response:**

```json
{
  "response": "I heard: 'Hello Sage'. You can teach me by saying: 'Learn that X means Y.'",
  "confidence": 0.7,
  "source": "simple"
}
```

---

## Example Interaction

```
User:  Learn that Python is my favorite language

Later...

User:  What language do I like?
Sage:  Python
```

This interaction demonstrates how the assistant can retain knowledge through the learning engine.

---

## Roadmap

Planned improvements include:

- Persistent memory storage using a database
- Retrieval-augmented responses using external documents
- Tool integrations (calculations, data queries)
- Multi-user conversation support
- Observability and logging
- Deployment-ready containerization

---

## Purpose of the Project

Sage-AI is intended as a systems engineering project exploring how conversational AI assistants can be structured internally.

The project focuses on building the underlying architecture of AI assistants — separating conversation handling, reasoning logic, and knowledge storage — rather than focusing solely on model responses.

This approach emphasizes modular design, clear system boundaries, and experimentation with conversational learning systems.
