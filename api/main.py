from __future__ import annotations
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import json
import os
import secrets
import logging
from pathlib import Path
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from auth.security import AuthManager, RBACManager
from monitoring.metrics import MetricsCollector, HealthChecker


logger = logging.getLogger("code-swarm.api")

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)

# --- Security configuration (CEO Audit fix) -----------------------------------
# SECRET_KEY MUST be supplied via environment in production. We refuse to start
# with the legacy hardcoded placeholder. In development, an ephemeral key is
# generated on boot so local runs still work, but tokens won't survive restarts.
_LEGACY_INSECURE_KEY = "code-swarm-secret-key-change-in-production"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
SECRET_KEY = os.getenv("SECRET_KEY", "").strip()

if not SECRET_KEY or SECRET_KEY == _LEGACY_INSECURE_KEY:
    if ENVIRONMENT == "production":
        raise RuntimeError(
            "SECRET_KEY environment variable is required in production "
            "and must not be the legacy default. Set a strong random value, "
            "e.g. `python -c 'import secrets; print(secrets.token_urlsafe(64))'`."
        )
    SECRET_KEY = secrets.token_urlsafe(64)
    logger.warning(
        "SECRET_KEY not set; generated an ephemeral development key. "
        "Tokens will be invalidated on restart. Set SECRET_KEY in your env "
        "for stable sessions."
    )

# CORS: production must declare explicit origins. Wildcard with credentials is
# rejected by browsers and is a security smell.
_raw_origins = os.getenv("ALLOWED_ORIGINS", "").strip()
if _raw_origins:
    ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]
else:
    if ENVIRONMENT == "production":
        raise RuntimeError(
            "ALLOWED_ORIGINS environment variable is required in production "
            "(comma-separated list of allowed origins, e.g. https://app.opensin.ai)."
        )
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
    ]
    logger.warning(
        "ALLOWED_ORIGINS not set; falling back to localhost development origins."
    )

BASE_DIR = Path(os.getenv("CODE_SWARM_BASE_DIR", "."))

auth_manager = AuthManager(secret_key=SECRET_KEY, base_dir=BASE_DIR)
rbac_manager = RBACManager(base_dir=BASE_DIR)
metrics = MetricsCollector(service_name="code-swarm-api")
health = HealthChecker(base_dir=BASE_DIR)


app = FastAPI(
    title="Code-Swarm API",
    description="SOTA Agent Swarm API with FastAPI + gRPC",
    version="1.0.0",
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc: HTTPException(status_code=429, detail="Rate limit exceeded"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


class AgentCreate(BaseModel):
    name: str
    model: str
    role: str
    capabilities: Optional[list[str]] = []


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: int = 5
    assigned_to: Optional[str] = None


class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@app.get("/health")
@limiter.limit("10/minute")
def health_check(request: Request):
    status = health.get_status()
    return {"status": "healthy" if status["healthy"] else "degraded", "details": status}


@app.get("/metrics")
@limiter.limit("5/minute")
def get_metrics(request: Request):
    return {"metrics": metrics.get_metrics()}


@app.post("/auth/token", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, token_request: TokenRequest):
    user = auth_manager.authenticate(token_request.username, token_request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = auth_manager.create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/auth/register")
@limiter.limit("3/minute")
def register(request: Request, username: str, password: str, role: str = "developer"):
    user = auth_manager.create_user(username, password, role)
    if not user:
        raise HTTPException(status_code=400, detail="User already exists")
    return {"username": user["username"], "role": user["role"]}


@app.post("/agents")
@limiter.limit("30/minute")
def create_agent(request: Request, agent: AgentCreate):
    agents_data = _load_agents()
    for a in agents_data:
        if a["name"] == agent.name:
            raise HTTPException(status_code=400, detail="Agent already exists")
    new_agent = {
        "id": f"agent_{len(agents_data)+1}",
        "name": agent.name,
        "model": agent.model,
        "role": agent.role,
        "capabilities": agent.capabilities,
        "status": "idle",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    agents_data.append(new_agent)
    _save_agents(agents_data)
    metrics.record_task(agent.name, "created", 0.0)
    return new_agent


@app.get("/agents")
@limiter.limit("100/minute")
def list_agents(request: Request):
    return _load_agents()


@app.get("/agents/{agent_id}")
@limiter.limit("100/minute")
def get_agent(request: Request, agent_id: str):
    agents = _load_agents()
    for a in agents:
        if a["id"] == agent_id:
            return a
    raise HTTPException(status_code=404, detail="Agent not found")


@app.post("/tasks")
@limiter.limit("30/minute")
def create_task(request: Request, task: TaskCreate):
    tasks_data = _load_tasks()
    new_task = {
        "id": f"task_{len(tasks_data)+1}",
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "assigned_to": task.assigned_to,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    tasks_data.append(new_task)
    _save_tasks(tasks_data)
    return new_task


@app.get("/tasks")
@limiter.limit("100/minute")
def list_tasks(request: Request, status: Optional[str] = None):
    tasks = _load_tasks()
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    return tasks


@app.patch("/tasks/{task_id}")
@limiter.limit("50/minute")
def update_task(request: Request, task_id: str, status: str):
    tasks = _load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            task["status"] = status
            if status == "completed":
                task["completed_at"] = datetime.now(timezone.utc).isoformat()
            _save_tasks(tasks)
            return task
    raise HTTPException(status_code=404, detail="Task not found")


def _load_agents():
    agents_file = Path(".code-swarm/agents.json")
    if agents_file.exists():
        return json.loads(agents_file.read_text())
    return []


def _save_agents(agents):
    agents_file = Path(".code-swarm/agents.json")
    agents_file.parent.mkdir(parents=True, exist_ok=True)
    agents_file.write_text(json.dumps(agents, indent=2))


def _load_tasks():
    tasks_file = Path(".code-swarm/tasks.json")
    if tasks_file.exists():
        return json.loads(tasks_file.read_text())
    return []


def _save_tasks(tasks):
    tasks_file = Path(".code-swarm/tasks.json")
    tasks_file.parent.mkdir(parents=True, exist_ok=True)
    tasks_file.write_text(json.dumps(tasks, indent=2))
