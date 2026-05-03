# Getting Started with Code-Swarm

## Installation

### Prerequisites
- Python 3.10+
- pip or poetry
- PostgreSQL (or Supabase)

### Step 1: Clone & Install

```bash
git clone https://github.com/OpenSIN-Code/Code-Swarm.git
cd Code-Swarm
pip install -e .
```

### Step 2: Configure Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and set your values:

```ini
# Supabase
SUPABASE_URL=postgresql://user:password@host:5432/code_swarm
REDIS_URL=redis://localhost:6379/0

# Simone-MCP (set this to your own Simone-MCP host, no default fallback)
SIMONE_MCP_URL=http://your-simone-host:8234
# or for local development:
# SIMONE_MCP_URL=http://localhost:8234

# API Security
SECRET_KEY=your-random-secret-key-here
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Models
PRIMARY_MODEL=gpt-4
VISION_MODEL=gpt-4-vision
```

### Step 3: Initialize Database

```bash
code-swarm db init
code-swarm db migrate
```

### Step 4: Start the API Server

```bash
code-swarm api --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000/docs` for interactive API docs.

## First Task

### Create an Agent

```bash
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "solver",
    "model": "gpt-4",
    "role": "backend",
    "capabilities": ["code-generation", "testing"]
  }'
```

### Assign a Task

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Fix the login endpoint",
    "description": "Add JWT token refresh mechanism",
    "priority": 8,
    "assigned_to": "solver"
  }'
```

### Monitor Execution

```bash
# Via WebSocket (real-time)
wscat -c ws://localhost:8000/ws/tasks/task_1

# Or via REST
curl http://localhost:8000/tasks/task_1
```

## Next Steps

- [Architecture Guide](architecture/overview.md) — Understand the system design
- [API Reference](api/rest.md) — Explore all endpoints
- [CLI Guide](guides/cli.md) — Master the command-line interface
- [Deployment Guide](guides/deployment-vercel.md) — Deploy to production

## Troubleshooting

**Q: Port 8000 already in use?**  
A: Use a different port: `code-swarm api --port 8001`

**Q: Simone-MCP not reachable?**  
A: Check SIMONE_MCP_URL in .env; ensure the OCI VM is running and accessible

**Q: Database connection failed?**  
A: Verify SUPABASE_URL format and credentials

Need help? [Open an issue](https://github.com/OpenSIN-Code/Code-Swarm/issues)
