# REST API Reference

## Base URL
```
http://localhost:8000
```

## Authentication

All endpoints (except `/health`) require a Bearer token:

```bash
# Get token
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Use token
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/agents
```

## Rate Limits

| Endpoint | Limit |
|---|---|
| `/auth/token` | 5/minute |
| `/auth/register` | 3/minute |
| `/agents` | 30/minute |
| `/tasks` | 30/minute |
| `/health` | 10/minute |

## Agents

### Create Agent
```
POST /agents
Content-Type: application/json

{
  "name": "solver",
  "model": "gpt-4",
  "role": "backend",
  "capabilities": ["code-generation", "testing"]
}
```

**Response (201):**
```json
{
  "id": "agent_1",
  "name": "solver",
  "model": "gpt-4",
  "role": "backend",
  "capabilities": ["code-generation", "testing"],
  "status": "idle",
  "created_at": "2026-05-03T10:00:00Z"
}
```

### List Agents
```
GET /agents
```

**Response (200):**
```json
[
  {
    "id": "agent_1",
    "name": "solver",
    "model": "gpt-4",
    "role": "backend",
    "status": "idle",
    "created_at": "2026-05-03T10:00:00Z"
  }
]
```

### Get Agent
```
GET /agents/{agent_id}
```

**Response (200):**
```json
{
  "id": "agent_1",
  "name": "solver",
  "model": "gpt-4",
  "role": "backend",
  "status": "active",
  "created_at": "2026-05-03T10:00:00Z"
}
```

## Tasks

### Create Task
```
POST /tasks
Content-Type: application/json

{
  "title": "Fix login endpoint",
  "description": "Add JWT token refresh",
  "priority": 8,
  "assigned_to": "solver"
}
```

**Response (201):**
```json
{
  "id": "task_1",
  "title": "Fix login endpoint",
  "description": "Add JWT token refresh",
  "priority": 8,
  "assigned_to": "solver",
  "status": "pending",
  "created_at": "2026-05-03T10:00:00Z"
}
```

### List Tasks
```
GET /tasks?status=pending
```

**Response (200):**
```json
[
  {
    "id": "task_1",
    "title": "Fix login endpoint",
    "status": "pending",
    "priority": 8,
    "created_at": "2026-05-03T10:00:00Z"
  }
]
```

### Update Task
```
PATCH /tasks/{task_id}
Content-Type: application/json

{"status": "completed"}
```

**Response (200):**
```json
{
  "id": "task_1",
  "title": "Fix login endpoint",
  "status": "completed",
  "completed_at": "2026-05-03T10:15:00Z"
}
```

## Health & Metrics

### Health Check
```
GET /health
```

**Response (200):**
```json
{
  "status": "healthy",
  "details": {
    "database": "connected",
    "cache": "connected",
    "simone_mcp": "connected"
  }
}
```

### Metrics
```
GET /metrics
```

**Response (200):**
```json
{
  "metrics": {
    "total_agents": 5,
    "total_tasks": 42,
    "avg_task_duration": "15.3s",
    "error_rate": "0.2%"
  }
}
```

## Error Responses

### 400 Bad Request
```json
{"detail": "Agent already exists"}
```

### 401 Unauthorized
```json
{"detail": "Invalid credentials"}
```

### 429 Too Many Requests
```json
{"detail": "Rate limit exceeded"}
```

### 404 Not Found
```json
{"detail": "Agent not found"}
```

### 500 Internal Server Error
```json
{"detail": "Internal server error"}
```

## Interactive Docs

Visit `http://localhost:8000/docs` for Swagger UI with try-it-out functionality.
