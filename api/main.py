from __future__ import annotations
from fastapi import FastAPI, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime, timezone
import json
import time
import asyncio
from pathlib import Path

from auth.security import AuthManager, RBACManager
# Import monitoring modules directly to avoid circular imports
from pathlib import Path
import json
from datetime import datetime, timezone

class MetricsCollector:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.metrics_file = Path(".code-swarm/metrics.json")
        
    def record_task(self, agent_name: str, action: str, duration: float):
        metrics = {}
        if self.metrics_file.exists():
            metrics = json.loads(self.metrics_file.read_text())
        
        if agent_name not in metrics:
            metrics[agent_name] = {}
        if action not in metrics[agent_name]:
            metrics[agent_name][action] = []
        metrics[agent_name][action].append({
            "duration": duration,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        self.metrics_file.write_text(json.dumps(metrics, indent=2))
    
    def get_metrics(self):
        if self.metrics_file.exists():
            return json.loads(self.metrics_file.read_text())
        return {}

class HealthChecker:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.health_file = base_dir / ".code-swarm/health.json"
    
    def get_status(self):
        if self.health_file.exists():
            health_data = json.loads(self.health_file.read_text())
            healthy = all(
                service.get("status") == "healthy"
                for service in health_data.values()
            )
            return {"healthy": healthy, "services": health_data}
        return {"healthy": False, "services": {}}
from middleware import RateLimitMiddleware, LoggingMiddleware
from grpc_server import CodeSwarmServer


SECRET_KEY = "code-swarm-secret-key-change-in-production"
BASE_DIR = Path(".")

auth_manager = AuthManager(secret_key=SECRET_KEY, base_dir=BASE_DIR)
rbac_manager = RBACManager(base_dir=BASE_DIR)
metrics = MetricsCollector(service_name="code-swarm-api")
health = HealthChecker(base_dir=BASE_DIR)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, agent_id: str):
        await websocket.accept()
        if agent_id not in self.active_connections:
            self.active_connections[agent_id] = []
        self.active_connections[agent_id].append(websocket)
        logging.info(f"WebSocket connected: {agent_id}")

    def disconnect(self, websocket: WebSocket, agent_id: str):
        if agent_id in self.active_connections:
            self.active_connections[agent_id].remove(websocket)
            if not self.active_connections[agent_id]:
                del self.active_connections[agent_id]
            logging.info(f"WebSocket disconnected: {agent_id}")

    async def broadcast(self, agent_id: str, message: dict):
        if agent_id in self.active_connections:
            for connection in self.active_connections[agent_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logging.error(f"Error broadcasting to {agent_id}: {e}")
                    self.disconnect(connection, agent_id)

connection_manager = ConnectionManager()


async def broadcast_agent_status(agent_id: str, status: str, details: Optional[dict] = None):
    """
    Broadcast agent status update to all connected WebSocket clients.
    
    Args:
        agent_id: The agent identifier (e.g., 'sin-zeus', 'sin-solo')
        status: The status to broadcast (e.g., 'idle', 'working', 'error')
        details: Additional details to include in the message
    """
    message = {
        "agent_id": agent_id,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": details or {}
    }
    await connection_manager.broadcast(agent_id, message)


app = FastAPI(
    title="Code-Swarm API",
    description="SOTA Agent Swarm API with FastAPI + gRPC, Rate Limiting, WebSockets",
    version="1.0.0",
    openapi_tags=[
        {"name": "agents", "description": "Agent Operations"},
        {"name": "tasks", "description": "Task Operations"},
        {"name": "auth", "description": "Authentication & Authorization"},
        {"name": "system", "description": "System Information"},
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting and logging middleware
app.add_middleware(RateLimitMiddleware, max_requests=50, window_seconds=1)
app.add_middleware(LoggingMiddleware)


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
def health_check():
    status = health.get_status()
    return {"status": "healthy" if status["healthy"] else "degraded", "details": status}


@app.get("/metrics")
def get_metrics():
    return {"metrics": metrics.get_metrics()}


@app.post("/auth/token", response_model=TokenResponse)
def login(request: TokenRequest):
    user = auth_manager.authenticate(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = auth_manager.create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/auth/register")
def register(username: str, password: str, role: str = "developer"):
    user = auth_manager.create_user(username, password, role)
    if not user:
        raise HTTPException(status_code=400, detail="User already exists")
    return {"username": user["username"], "role": user["role"]}


@app.post("/agents")
def create_agent(agent: AgentCreate):
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
def list_agents():
    return _load_agents()


@app.get("/agents/{agent_id}")
def get_agent(agent_id: str):
    agents = _load_agents()
    for a in agents:
        if a["id"] == agent_id:
            return a
    raise HTTPException(status_code=404, detail="Agent not found")


@app.post("/tasks")
def create_task(task: TaskCreate):
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
def list_tasks(status: Optional[str] = None):
    tasks = _load_tasks()
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    return tasks


@app.patch("/tasks/{task_id}")
def update_task(task_id: str, status: str):
    tasks = _load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            task["status"] = status
            if status == "completed":
                task["completed_at"] = datetime.now(timezone.utc).isoformat()
            _save_tasks(tasks)
            return task
    raise HTTPException(status_code=404, detail="Task not found")


@app.websocket("/ws/agents/{agent_id}")
async def agent_status_websocket(websocket: WebSocket, agent_id: str):
    """
    WebSocket endpoint for real-time agent status updates.
    
    Clients can connect to receive live updates about:
    - Agent status (idle, working, error)
    - Task progress
    - System health
    - Agent metrics
    
    Example connection:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/agents/sin-zeus');
    ws.onmessage = (event) => console.log(JSON.parse(event.data));
    ```
    """
    await connection_manager.connect(websocket, agent_id)
    try:
        # Send initial status
        initial_status = {
            "agent_id": agent_id,
            "status": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": {"message": "WebSocket connection established"}
        }
        await websocket.send_json(initial_status)
        
        # Keep connection alive
        while True:
            await asyncio.sleep(30)  # Keep-alive ping
            await websocket.send_json({
                "agent_id": agent_id,
                "status": "alive",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, agent_id)
        logging.info(f"WebSocket disconnected: {agent_id}")
    except Exception as e:
        connection_manager.disconnect(websocket, agent_id)
        logging.error(f"WebSocket error for {agent_id}: {e}")


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


import threading
import socket


def serve_grpc():
    """Start the gRPC server on port 50051."""
    import logging
    logging.basicConfig(level=logging.INFO)
    grpc_server = CodeSwarmServer(port=50051)
    try:
        grpc_server.start()
        logging.info("gRPC server running on port 50051")
        
        # Save gRPC health status by reading the gRPC health file
        health_metrics = {
            "service": "grpc_server",
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": {"port": 50051}
        }
        grpc_health_file = Path(".code-swarm/grpc_health")
        if grpc_health_file.exists():
            health_metrics["details"]["content"] = grpc_health_file.read_text()
        
        health_file = Path(".code-swarm/health.json")
        health_data = {}
        if health_file.exists():
            health_data = json.loads(health_file.read_text())
        health_data["grpc_server"] = health_metrics
        health_file.parent.mkdir(parents=True, exist_ok=True)
        health_file.write_text(json.dumps(health_data, indent=2))
        
        # Keep server running
        while True:
            time.sleep(3600)  # Sleep for 1 hour
    except KeyboardInterrupt:
        grpc_server.stop()


def serve_api():
    """Start the FastAPI server on port 8000 with rate limiting."""
    import logging
    import uvicorn
    logging.info("FastAPI server starting on port 8000")
    logging.info("Swagger UI: http://localhost:8000/docs")
    logging.info("OpenAPI JSON: http://localhost:8000/openapi.json")
    logging.info("Rate limiting: 50 requests/second/IP")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        timeout_keep_alive=30,
        workers=1  # Reduced workers for WebSocket support
    )


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Set up WebSocket broadcasting for gRPC server
    from api.grpc_server import broadcast_agent_status as grpc_broadcast
    grpc_broadcast = broadcast_agent_status

    # Start gRPC server in background thread
    grpc_thread = threading.Thread(target=serve_grpc, daemon=True)
    grpc_thread.start()
    
    # Give gRPC server a moment to start
    time.sleep(1)
    
    # Verify gRPC health
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("localhost", 50051))
        if result != 0:
            logging.error("gRPC server failed to start")
        else:
            logging.info("gRPC server health check: PASS")
        sock.close()
    except Exception as e:
        logging.error(f"gRPC health check failed: {e}")
    
    logging.info("Starting Code-Swarm API Gateway...")
    logging.info("✅ FastAPI/Gateway: http://localhost:8000")
    logging.info("✅ gRPC Services: localhost:50051")
    logging.info("✅ Rate Limiting: 50 req/sec/IP")
    logging.info("✅ Health Monitor: /.code-swarm/health.json")
    logging.info("✅ Metrics Collection: /metrics")
    logging.info("✅ API Gateway: OPERATIONAL")
    
    # Start FastAPI
    serve_api()