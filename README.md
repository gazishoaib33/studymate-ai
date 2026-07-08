# StudyMate AI

AI-powered study assistant: upload lecture PDFs, chat with them (RAG), get summaries,
quizzes, and flashcards. Built with a fully free/local AI stack (Ollama + Sentence-Transformers
+ ChromaDB) so it costs nothing to run or develop.

## Status: Module 3 -- Frontend + RAG Chat

Backend now includes:
- Auth (register/login, JWT)
- Subjects (create/list, scoped per user)
- Documents (PDF upload, background ingestion: extract -> chunk -> embed -> ChromaDB)
- **RAG chat** (`/api/v1/chat/`) -- retrieval + Ollama streaming + citations, saved to Postgres

Frontend (`frontend/`) is a React + TypeScript + Vite + Tailwind app:
- Login / Register
- Dashboard -- create subjects, see them as a shelf of cards
- Subject page -- upload PDFs, see live processing status, start a chat once ready
- Chat page -- streaming answers with citation tabs (styled as bookmark tabs, click to preview the source excerpt)

## Running the frontend

The frontend runs on your host machine (not inside Docker) since it just needs Node + Vite dev server, and this keeps hot-reload fast:

```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:5173. It talks to the backend at `http://localhost:8000` (hardcoded in `src/lib/api.ts` -- fine for local dev, would become an env var for real deployment).

Make sure the Docker backend stack (`docker compose up`) is running first, and that you've registered/logged in at least once (uses `localStorage` for the JWT).

## Roadmap

- [x] Module 1 -- Foundation
- [x] Module 2 -- PDF ingestion + RAG pipeline (chunking, embeddings, retrieval)
- [x] Module 3 -- RAG chat endpoint (streaming + citations) + frontend
- [ ] Module 4 -- Summarizer, quiz generator, flashcards
- [ ] Module 5 -- Scale/hardening (Celery, OCR, rate limiting, analytics)
- [ ] Module 6 -- Research extension (eval harness, benchmarks, writeup)

## Prerequisites

- Docker + Docker Compose installed
- ~8GB RAM free (Ollama models need it) and a few GB disk space for the model

## Setup (run on your machine)

```bash
# 1. Clone / cd into the project
cd studymate-ai

# 2. Create your local env file
cp .env.example .env
# Edit .env if you want, but the defaults work out of the box

# 3. Start everything
docker compose up --build
```

This starts 4 containers: `studymate-postgres`, `studymate-chroma`, `studymate-ollama`,
`studymate-backend`.

## Pull the local LLM (one-time, after containers are up)

```bash
docker exec -it studymate-ollama ollama pull llama3.1:8b
```

(Swap for a smaller model like `qwen2.5:3b` or `phi3:mini` if your machine is low on RAM.)

## Verify it's working

- API root: http://localhost:8000/ 
- Interactive API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/v1/health
- DB connectivity check: http://localhost:8000/api/v1/health/db

## Run database migrations

Once the containers are up, in a **second terminal**:

```bash
docker exec -it studymate-backend alembic revision --autogenerate -m "init tables"
docker exec -it studymate-backend alembic upgrade head
```

This creates the `users`, `subjects`, `documents`, `embeddings`, `chats`, `messages` tables.

## Project structure

```
backend/
  app/
    api/            # FastAPI routers (HTTP layer only, no business logic)
    core/           # settings, security (JWT/password hashing)
    db/             # SQLAlchemy engine/session/base
    domain/         # abstract interfaces (LLMProvider, EmbeddingProvider, VectorStore)
    models/         # SQLAlchemy ORM models
    schemas/        # Pydantic request/response schemas
    services/       # business logic (added in Module 2+)
    repositories/   # DB access layer (added in Module 2+)
    infra/          # concrete adapters: llm/, embeddings/, vectorstore/ (Module 2)
  alembic/          # DB migrations
frontend/           # React app (Module 3)
```

## Push to GitHub

```bash
git init
git add .
git commit -m "Module 1: foundation - docker compose, db models, health checks"
git branch -M main
git remote add origin https://github.com/<your-username>/studymate-ai.git
git push -u origin main
```

`.env` is gitignored -- never commit real secrets. `.env.example` is the template
collaborators (and future-you) copy from.
