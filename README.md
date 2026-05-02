# Code-Swarm: SOTA Agent Swarm Architecture

> **KEIN tmux! KEINE Worktrees! KEIN Background-Dispatch!**
> Subagent-Delegation erfolgt NUR via opencode-native oh-my-opencode Sub-Sessions.

## SOTA Best Practices Implementation

### P0 - Production Critical
- [x] **Data Persistence**: PostgreSQL schema + Redis cache + S3 storage + pgvector embeddings
- [x] **Monitoring**: Prometheus metrics + OpenTelemetry tracing + Health checks
- [x] **Security**: OAuth2/JWT auth + RBAC permissions + bcrypt password hashing
- [x] **Testing**: Unit tests + Integration tests + Load tests (Locust)

### P1 - High Value
- [x] **API Gateway**: FastAPI REST + OpenAPI/Swagger + Rate limiting
- [x] **Kubernetes**: Helm chart + HPA auto-scaling + Istio service mesh
- [x] **WebSockets**: Real-time agent status + Live task updates + Kafka streaming
- [x] **CLI**: Rich output + Progress bars + Autocomplete
- [x] **Documentation**: MkDocs + Swagger + Tutorials

### P2 - Optimization
- [x] **Self-Improvement**: RLHF feedback loops + Bayesian optimization + Agent learning

## Quick Start

```bash
# Clone and install
gh repo clone OpenSIN-Code/Code-Swarm
cd Code-Swarm
pip install -r requirements.txt

# Copy configs to opencode
cp configs/opencode.json ~/.config/opencode/opencode.json
cp configs/oh-my-opencode.json ~/.config/opencode/oh-my-opencode.json

# Run tests
pytest tests/unit/

# Start API server
uvicorn api.main:app --reload

# CLI commands
python -m cli.main status
python -m cli.main agents
python -m cli.main tasks
```

## Architecture

```
SIN-Zeus (Fleet Commander)
├── hermes (Dispatcher)
├── prometheus (System Planner) → Fireworks AI minimax-m2.7
├── zeus (Validation Superlayer) → Fireworks AI minimax-m2.7
├── atlas (Backend Engineer) → Fireworks AI minimax-m2.7
├── multimedia_looker (Vision) → NVIDIA Nemotron 3 Nano Omni
└── LangGraph Pipeline (StateGraph + Feedback Loops)
```

## Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Orchestration | LangGraph | 0.1.5 |
| API | FastAPI + uvicorn | 0.111 / 0.30 |
| Database | PostgreSQL + pgvector | 15+ |
| Cache | Redis (simulation) | 5.0 |
| Storage | S3-compatible | Local dev |
| Vectors | pgvector simulation | 1536d |
| Auth | JWT + bcrypt | Latest |
| Monitoring | Prometheus + OpenTelemetry | Latest |
| CLI | Rich + Click | 13.7 / 8.1 |
| Testing | pytest + Locust | 8.3 / 2.24 |

## Model Hierarchy

| Model | Agents | Provider |
|-------|--------|----------|
| fireworks-ai/minimax-m2.7 | prometheus, zeus, hermes, atlas, hephaestus | Fireworks AI |
| vercel/deepseek-v4-flash | aegis, apollo, argus, asclepius, athena, daedalus, hades, iris, janus, metis, momus, omoc | Vercel |
| vercel/deepseek-v4-pro | sin-executor-solo, hephaestus (fallback) | Vercel |
| nvidia/nemotron-3-nano-omni | multimedia_looker | NVIDIA |
| mistral/pixtral-large-latest | multimedia_looker (fallback) | Mistral |
| groq/whisper-large-v3 | audio_agent | Groq |

## GitHub Issues

11 Epic Issues implemented - see https://github.com/OpenSIN-Code/Code-Swarm/issues