# Agentic AI Research Assistant on Azure

Production-grade, multi-agent RAG platform for PDF-grounded research Q and A with explainable traces, streaming responses, and Azure-native container deployment.

## Tech Stack & Skills

### Languages and Runtime
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white) ![JavaScript](https://img.shields.io/badge/JavaScript-ES202x-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black) ![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white) ![YAML](https://img.shields.io/badge/YAML-CB171E?style=for-the-badge&logo=yaml&logoColor=white)

### AI, LLM, and RAG Frameworks
![LangGraph](https://img.shields.io/badge/LangGraph-Graph%20Orchestration-1C3A5F?style=for-the-badge) ![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white) ![Groq](https://img.shields.io/badge/Groq%20API-F55036?style=for-the-badge&logo=groq&logoColor=white) ![HuggingFace](https://img.shields.io/badge/HuggingFace-FFCC4D?style=for-the-badge&logo=huggingface&logoColor=black) ![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white) ![ChromaDB](https://img.shields.io/badge/ChromaDB-6E56CF?style=for-the-badge)

### Backend and API
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white) ![Uvicorn](https://img.shields.io/badge/Uvicorn-Server-4051B5?style=for-the-badge) ![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white) ![SQLModel](https://img.shields.io/badge/SQLModel-ORM-0F172A?style=for-the-badge)

### Frontend
![React](https://img.shields.io/badge/React-18-20232A?style=for-the-badge&logo=react&logoColor=61DAFB) ![React Router](https://img.shields.io/badge/React%20Router-CA4245?style=for-the-badge&logo=reactrouter&logoColor=white) ![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white) ![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)

### Infrastructure, DevOps, and Cloud
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white) ![Nginx](https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white) ![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white) ![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white) ![Microsoft Azure](https://img.shields.io/badge/Azure-0078D4?style=for-the-badge&logo=microsoftazure&logoColor=white)

---

## Multi-Agent Architecture (Code-Accurate)

```mermaid
flowchart TD
		U[User] --> Q[/POST /api/query or /api/query/stream/]
		Q --> G[LangGraph app_graph]

		G --> R[Router Agent]
		R -->|datasource = vectorstore| RET[Retriever Agent]
		R -->|datasource = direct_chat| GEN[Generator Agent]

		RET --> RANK[Ranker Agent]
		RANK --> GEN
		GEN --> CRI[Critic Agent]

		CRI -->|is_valid = yes| DONE[Final answer + trace]
		CRI -->|is_valid = no and loop_count < 2| GEN
		CRI -->|loop_count >= 2| DONE

		subgraph Shared System Tools
			VM[VectorStoreManager]
			CH[(Chroma collections by chat_id)]
			EMB[HuggingFaceEmbeddings]
			DB[(SQLite via SQLModel)]
			UP[Background upload job store]
			TB[Token budget and fallback logic]
			RL[In-memory rate limiter]
		end

		RET --> VM
		VM --> CH
		VM --> EMB
		Q --> DB
		Q --> UP
		GEN --> TB
		Q --> RL
```

[🔍 View Technical Details in Documentation](documentation.md#multi-agent-architecture)

---

## 🧱 Phase 1: Dockerization and Registry (ACR)

The project is packaged as two containers:
- Backend container on Python 3.11 slim with ML and RAG dependencies.
- Frontend container with a multi-stage build (Node build stage + Nginx runtime stage).

Heavy-image strategy:
- Keep requirements installation before app source copy to improve Docker cache reuse.
- Push immutable image tags in CI for safe roll-forward and rollback.

### Docker Compose Runtime Snapshot
![Docker containers](<screenshots/docker containers.png>)

[🔍 View Technical Details in Documentation](documentation.md#phase-1-dockerization-and-registry-acr)

---

## 🔁 Phase 2: CI/CD Automation (GitHub Actions)

Pipeline behavior from the workflow:
1. Run backend tests with environment variables suitable for CI.
2. Authenticate to Azure.
3. Authenticate to ACR.
4. Build and push backend and frontend images tagged with commit SHA.
5. Deploy both services to Azure Container Apps.

### CI/CD Pipeline Evidence
![CI/CD GitHub Actions](<screenshots/cicd github.png>)

[🔍 View Technical Details in Documentation](documentation.md#phase-2-cicd-automation)

---

## ☁️ Phase 3: Azure Infrastructure

Provisioned cloud boundary:
- Resource group scoped in Spain Central.
- Shared Container Apps environment.
- Separate backend and frontend Container Apps.
- ACR-backed image source.

### Global Resource Group View
![Azure resource list overview](screenshots/azure-resource-list-overview.png)

[🔍 View Technical Details in Documentation](documentation.md#phase-3-azure-infrastructure)

### Backend Container App Overview
![Backend overview](screenshots/azure-containerapp-overview-backend.png)

[🔍 View Technical Details in Documentation](documentation.md#phase-3-azure-infrastructure)

### Frontend Container App Overview
![Frontend overview](screenshots/azure-containerapp-overview-frontend.png)

[🔍 View Technical Details in Documentation](documentation.md#phase-3-azure-infrastructure)

### Frontend Dashboard (Start/Stop)
![Frontend dashboard start stop](screenshots/azure-containerapp-frontend-dashboard.png)

[🔍 View Technical Details in Documentation](documentation.md#phase-3-azure-infrastructure)

### Public Azure Deployment Validation
![Deployed Azure app](<screenshots/deployed azure app.png>)

[🔍 View Technical Details in Documentation](documentation.md#phase-3-azure-infrastructure)

---

## 🌐 Phase 4: Networking, Nginx Reverse Proxy, and Application UX Validation

Network behavior implemented:
- SPA fallback through try_files for React routes.
- Reverse proxy from frontend /api to backend HTTPS endpoint on Azure Container Apps.
- TLS SNI fix using proxy_ssl_server_name on; for Azure certificate hostname validation.

### Main Interface (Forest Theme)
![Main page forest theme](<screenshots/research ai main page (foret emeraude theme).png>)

[🔍 View Technical Details in Documentation](documentation.md#phase-4-networking-and-nginx)

### Theme Variant: Sombre Classique
![Sombre classique](<screenshots/sombre classique.png>)

[🔍 View Technical Details in Documentation](documentation.md#phase-4-networking-and-nginx)

### Theme Variant: Clair Épuré
![Clair epure theme](<screenshots/clair epure theme.png>)

[🔍 View Technical Details in Documentation](documentation.md#phase-4-networking-and-nginx)

### Theme Variant: Océan Profond
![Ocean profond theme](<screenshots/ocean profond theme.png>)

[🔍 View Technical Details in Documentation](documentation.md#phase-4-networking-and-nginx)

### Theme Variant: Néon Cyber
![Neon cyber theme](<screenshots/neon cyber theme.png>)

[🔍 View Technical Details in Documentation](documentation.md#phase-4-networking-and-nginx)

### Multi-PDF Upload Experience
![Upload multi fichiers](<screenshots/upload multi fichiers.png>)

[🔍 View Technical Details in Documentation](documentation.md#phase-4-networking-and-nginx)

### Grounded Q and A Result with Citations
![Question on uploaded docs and answer](<screenshots/question sur doc uploade(cv  et reponse).png>)

[🔍 View Technical Details in Documentation](documentation.md#multi-agent-architecture)

### Agent Trace and Reasoning Visibility
![Thought process et analyse des agents](<screenshots/thought process et analyse des agents.png>)

[🔍 View Technical Details in Documentation](documentation.md#multi-agent-architecture)

### Conversation Deletion Flow
![Suppression de conversation](<screenshots/supression de conversation.png>)

[🔍 View Technical Details in Documentation](documentation.md#phase-4-networking-and-nginx)

---

## 💸 Phase 5: Cost Control and Hibernation (Scale to 0)

Student-cost strategy:
- Keep min replicas at 0 when idle.
- Use bounded max replicas to avoid accidental burst cost.
- Resume with explicit scale update before demos.

### Revisions and Scaling Controls
![Azure containerapp revisions](screenshots/azure-containerapp-revisions.png)

[🔍 View Technical Details in Documentation](documentation.md#phase-5-cost-control-and-hibernation)

### Zero-Replica Operational Confirmation
![Azure containerapp details](screenshots/azure-containerapp-details.png)

[🔍 View Technical Details in Documentation](documentation.md#phase-5-cost-control-and-hibernation)

---

## Local Run

```bash
docker compose up --build -d
```

Endpoints:
- Frontend: http://localhost
- API: http://localhost:8000
- OpenAPI: http://localhost:8000/docs

Backend tests:

```bash
cd backend
pytest -q
```
