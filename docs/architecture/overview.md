# Architecture Overview

## System Design

Code-Swarm is built on three core pillars:

### 1. **Multi-Agent Orchestration** (LangGraph)
- Stateful agent workflows
- Conditional routing between agents
- Checkpointing & recovery
- Memory management

### 2. **Symbol-Safe Code Operations** (Simone-MCP)
- AST-level code edits (not diff-based)
- Find definitions, references, usages
- Replace function bodies safely
- Insert code without breaking syntax

### 3. **Persistent State** (Supabase PostgreSQL)
- Agent configuration
- Task history
- User authentication
- Execution logs

## Agent Personas

### Zeus (Architect)
- **Role:** System design & planning
- **Skills:** Architecture analysis, technical strategy
- **Simone-MCP Usage:** Project overview, symbol analysis

### Atlas (Backend)
- **Role:** Server & database development
- **Skills:** Code generation, testing, debugging
- **Simone-MCP Usage:** Code insertion, body replacement

### Iris (Frontend)
- **Role:** UI/UX implementation
- **Skills:** Component design, CSS, interactivity
- **Simone-MCP Usage:** Symbol replacement, reference finding

### Prometheus (Planning)
- **Role:** Requirement analysis & roadmapping
- **Skills:** Decomposition, prioritization
- **Simone-MCP Usage:** Code overview, impact analysis

### Hermes (Coordination)
- **Role:** Task distribution & status tracking
- **Skills:** Workflow orchestration, feedback loops
- **Simone-MCP Usage:** Status queries, symbol tracking

## Data Flow

```
Task Request
    ↓
[API] POST /tasks
    ↓
[Hermes] Task Distribution
    ↓
[Prometheus] Requirement Analysis
    ↓
[Zeus] Architecture Planning
    ↓
[Atlas] Backend Development ← Simone-MCP (find_symbol, replace_symbol_body)
    ↓
[Iris] Frontend Development ← Simone-MCP (insert_after_symbol, find_references)
    ↓
[Validation Layer] Testing & Quality Checks
    ↓
[Supabase] Store Results
    ↓
[WebSocket] Broadcast Status to Clients
    ↓
Task Complete
```

## Integration Points

### REST API
- Create/list agents and tasks
- Trigger workflows
- Retrieve results

### gRPC API
- High-performance agent communication
- Streaming results
- Bidirectional status updates

### WebSocket
- Real-time agent status
- Live task progress
- Error notifications

### Simone-MCP Bridge
- AST-based code analysis
- Symbol manipulation
- Project structure analysis

### Supabase
- PostgreSQL data persistence
- Authentication (JWT via Supabase Auth)
- Real-time subscriptions

## Deployment Model

### Development
- Local SQLite or Supabase
- Single-process execution
- Console logging

### Production
- Supabase PostgreSQL (managed)
- Vercel Serverless Functions
- Prometheus + Grafana monitoring
- Sentry error tracking

## Security Architecture

- **Authentication:** JWT tokens via Supabase Auth
- **Authorization:** RBAC (Role-Based Access Control)
- **Rate Limiting:** slowapi middleware (10-100 req/min per endpoint)
- **Data Encryption:** TLS in transit, AES at rest (Supabase default)
- **Secrets Management:** Environment variables, no hardcoded credentials

## Performance Targets

| Metric | Target |
|---|---|
| API p99 latency | <500ms |
| Task execution | <60s average |
| Concurrent users | 1,000+ |
| SWE-bench score | >40% (goal) |

Last updated: 2026-05-03
