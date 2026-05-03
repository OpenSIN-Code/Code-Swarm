from __future__ import annotations
from fastapi import FastAPI, HTTPException, Depends, Request, WebSocket, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import WebSocketException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Optional
from datetime import datetime, timezone
import os
import secrets
import logging
from pathlib import Path
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from auth.security import AuthManager, RBACManager
from monitoring.metrics import MetricsCollector, HealthChecker
from streaming.websocket import manager as ws_manager, verify_ws_token
from db.database import get_database, close_database

logger = logging.getLogger("code-swarm.api")

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)

# --- Security configuration (CEO Audit fix) -----------------------------------
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


# Lifespan for database initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db = get_database()
    await db.initialize()
    logger.info("Database initialized at startup")
    yield
    # Shutdown
    await close_database()
    logger.info("Database closed at shutdown")


app = FastAPI(
    title="Code-Swarm API",
    description="Production SOTA Agent Swarm API with PostgreSQL + LangGraph",
    version="1.0.0",
    lifespan=lifespan,
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


# ============================================================================
# MODELS
# ============================================================================

class AgentCreate(BaseModel):
    name: str
    model: str
    role: str
    capabilities: Optional[list[str]] = []
    metadata: Optional[dict] = None


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: int = 5
    assigned_to: Optional[str] = None


class TaskUpdate(BaseModel):
    status: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None
    score: Optional[float] = None


class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AgentResponse(BaseModel):
    id: str
    name: str
    model: str
    role: str
    status: str
    capabilities: list[str]


class TaskResponse(BaseModel):
    id: str
    title: str
    status: str
    priority: int
    assigned_to: Optional[str]
    created_at: str


# ============================================================================
# HEALTH & METRICS
# ============================================================================

@app.get("/health")
@limiter.limit("10/minute")
async def health_check(request: Request):
    status = health.get_status()
    return {"status": "healthy" if status["healthy"] else "degraded", "details": status}


@app.get("/metrics")
@limiter.limit("5/minute")
async def get_metrics(request: Request):
    db = get_database()
    db_metrics = await db.get_metrics()
    return {
        "metrics": {
            **metrics.get_metrics(),
            **db_metrics
        }
    }


# ============================================================================
# AUTHENTICATION
# ============================================================================

@app.post("/auth/token", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, token_request: TokenRequest):
    """Login and get JWT token."""
    user = auth_manager.authenticate(token_request.username, token_request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = auth_manager.create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/auth/register")
@limiter.limit("3/minute")
async def register(request: Request, username: str, password: str, role: str = "developer"):
    """Register new user."""
    user = auth_manager.create_user(username, password, role)
    if not user:
        raise HTTPException(status_code=400, detail="User already exists")
    return {"username": user["username"], "role": user["role"]}


# ============================================================================
# AGENTS
# ============================================================================

@app.post("/agents", response_model=AgentResponse)
@limiter.limit("30/minute")
async def create_agent(request: Request, agent: AgentCreate):
    """Create a new agent."""
    db = get_database()
    try:
        new_agent = await db.create_agent(
            name=agent.name,
            model=agent.model,
            role=agent.role,
            capabilities=agent.capabilities or [],
            metadata=agent.metadata or {},
        )
        metrics.record_task(f"agent.create.{agent.role}", "success", 0.0)
        return {
            "id": new_agent.id,
            "name": new_agent.name,
            "model": new_agent.model,
            "role": new_agent.role,
            "status": new_agent.status,
            "capabilities": new_agent.capabilities,
        }
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/agents", response_model=list[AgentResponse])
@limiter.limit("100/minute")
async def list_agents(request: Request, role: Optional[str] = None):
    """List all agents, optionally filtered by role."""
    db = get_database()
    agents = await db.list_agents(role=role)
    return [
        {
            "id": a.id,
            "name": a.name,
            "model": a.model,
            "role": a.role,
            "status": a.status,
            "capabilities": a.capabilities,
        }
        for a in agents
    ]


@app.get("/agents/{agent_id}", response_model=AgentResponse)
@limiter.limit("100/minute")
async def get_agent(request: Request, agent_id: str):
    """Get agent by ID."""
    db = get_database()
    agent = await db.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {
        "id": agent.id,
        "name": agent.name,
        "model": agent.model,
        "role": agent.role,
        "status": agent.status,
        "capabilities": agent.capabilities,
    }


# ============================================================================
# TASKS
# ============================================================================

@app.post("/tasks", response_model=TaskResponse)
@limiter.limit("30/minute")
async def create_task(request: Request, task: TaskCreate):
    """Create a new task."""
    db = get_database()
    try:
        new_task = await db.create_task(
            title=task.title,
            description=task.description,
            priority=task.priority,
            assigned_to=task.assigned_to,
        )
        metrics.record_task("task.create", "success", 0.0)
        return {
            "id": new_task.id,
            "title": new_task.title,
            "status": new_task.status,
            "priority": new_task.priority,
            "assigned_to": new_task.assigned_to,
            "created_at": new_task.created_at,
        }
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/tasks", response_model=list[TaskResponse])
@limiter.limit("100/minute")
async def list_tasks(request: Request, status: Optional[str] = None, assigned_to: Optional[str] = None):
    """List tasks with optional filters."""
    db = get_database()
    tasks = await db.list_tasks(status=status, assigned_to=assigned_to)
    return [
        {
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "priority": t.priority,
            "assigned_to": t.assigned_to,
            "created_at": t.created_at,
        }
        for t in tasks
    ]


@app.get("/tasks/{task_id}", response_model=TaskResponse)
@limiter.limit("100/minute")
async def get_task(request: Request, task_id: str):
    """Get task by ID."""
    db = get_database()
    task = await db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "id": task.id,
        "title": task.title,
        "status": task.status,
        "priority": task.priority,
        "assigned_to": task.assigned_to,
        "created_at": task.created_at,
    }


@app.patch("/tasks/{task_id}", response_model=TaskResponse)
@limiter.limit("50/minute")
async def update_task(request: Request, task_id: str, task_update: TaskUpdate):
    """Update task status/result/error."""
    db = get_database()
    try:
        updated_task = await db.update_task(
            task_id,
            status=task_update.status,
            result=task_update.result,
            error=task_update.error,
            score=task_update.score,
        )
        if not updated_task:
            raise HTTPException(status_code=404, detail="Task not found")
        metrics.record_task(f"task.update.{task_update.status}", "success", 0.0)
        return {
            "id": updated_task.id,
            "title": updated_task.title,
            "status": updated_task.status,
            "priority": updated_task.priority,
            "assigned_to": updated_task.assigned_to,
            "created_at": updated_task.created_at,
        }
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# WEBSOCKET STATS
# ============================================================================

@app.get("/ws/stats")
@limiter.limit("10/minute")
async def get_websocket_stats(request: Request):
    """Get WebSocket connection statistics."""
    return {
        "total_connections": ws_manager.get_connection_count(),
        "active_users": len(ws_manager.active_connections),
        "rate_limit_window": ws_manager.rate_limit_window,
        "rate_limit_max": ws_manager.rate_limit_max,
        "max_queue_size": ws_manager.max_message_queue
    }


# ============================================================================
# DEPRECATED: Legacy JSON-based endpoints (for backward compat during migration)
# These will be removed in v1.1.0
# ============================================================================

logger.info("Code-Swarm API v1.0.0 started with PostgreSQL persistence")
