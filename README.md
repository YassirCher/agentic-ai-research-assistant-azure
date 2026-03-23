# Agentic AI Research Assistant

A production-oriented, multi-agent research assistant for document-grounded Q&A.

The platform combines retrieval-augmented generation (RAG), async document ingestion, and an explainable multi-agent workflow to deliver accurate answers with citations.

## Overview

This project is designed as a SaaS-style application with:
- Isolated chat sessions and per-chat vector collections
- Multi-file PDF ingestion with background indexing
- Citation-aware answer generation
- Traceable agent steps (Router, Retriever, Ranker, Generator, Critic)
- Dockerized deployment and CI pipeline support

## Tech Stack

- Backend: FastAPI, LangGraph, LangChain, SQLModel (SQLite)
- Frontend: React (Vite), React Router, Nginx (containerized serving)
- Embeddings: PyTorch + sentence-transformers (`all-MiniLM-L6-v2`)
- Vector Store: ChromaDB
- LLM Provider: Groq
- DevOps: Docker Compose, GitHub Actions

## Core Features

- Multi-agent RAG orchestration with observable traces
- Asynchronous upload pipeline (`202 Processing`) with status polling
- Chunk filtering and batched vector insertion for better runtime stability
- Session-level data isolation (`chat_id`) for both SQL history and vector data
- Premium UI workflow (chat navigation, upload progress, deletion modal)

## Run Locally with Docker

Prerequisites:
- Docker Desktop (or Docker Engine + Compose plugin)

From the project root:

```bash
docker compose up --build -d
```

Endpoints:
- Application: http://localhost
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

Stop the stack:

```bash
docker compose down
```

## Backend Test Command

```bash
cd backend
pytest -q
```

## Repository Structure (High Level)

- `backend/`: FastAPI app, multi-agent graph, vector pipeline, tests
- `frontend/`: React app and containerized Nginx serving configuration
- `docker-compose.yml`: Local orchestration for backend/frontend and persistent volumes
- `.github/workflows/ci.yml`: CI workflow (tests + Docker build checks)

## Notes

- Runtime data persistence is handled via Docker volumes for SQLite and ChromaDB.
- The project is optimized for local Docker execution and cloud-container migration paths.
