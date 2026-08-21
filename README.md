# Vensora

Enterprise AI Customer Connect Platform designed for the logistics industry to provide AI-powered customer support through voice conversations.

## Phase 1 Architecture

Vensora is built as a **Modular Monolith**, ensuring clean logical boundaries for a seamless transition to microservices in Phase 2.

### Technology Stack

**Frontend**
- Next.js 15
- React 19
- TypeScript
- Tailwind CSS
- shadcn/ui

**Backend**
- FastAPI
- Python 3.12
- PostgreSQL
- Redis
- MinIO

**AI & Voice**
- LangGraph
- Groq
- Qdrant (BAAI BGE-M3)
- Faster Whisper (STT)
- Piper TTS
- Asterisk (SIP/RTP)

**Infrastructure**
- Docker Compose
- Nginx
- Prometheus, Grafana, Loki (Monitoring)

## Workspace Structure

```
vensora/
├── apps/
│   ├── web/        # Next.js frontend
│   └── backend/    # FastAPI modular monolith
├── packages/
│   ├── shared/     # Shared logic/types
│   ├── contracts/  # API contracts
│   ├── config/     # Base configuration
│   ├── logger/     # Shared logging format
│   └── ui/         # Shared UI components
├── infrastructure/
│   ├── docker/     # Dockerfiles and Compose configurations
│   └── nginx/      # Reverse proxy configuration
├── docs/           # Technical documentation (architecture, ADRs, API, etc.)
└── scripts/        # Automation and CI/CD scripts
```
