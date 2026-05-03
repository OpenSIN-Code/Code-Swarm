from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid
from enum import Enum


class AgentStatus(Enum):
    IDLE = "idle"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Agent:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    model: str = ""
    fallback_model: Optional[str] = None
    role: str = ""
    status: AgentStatus = AgentStatus.IDLE
    capabilities: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_seen_at: Optional[str] = None


@dataclass
class Session:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    swarm_id: str = "code-swarm"
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    status: str = "active"
    context: dict = field(default_factory=dict)
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    ended_at: Optional[str] = None
    duration_ms: Optional[int] = None
    error_count: int = 0
    metrics: dict = field(default_factory=dict)


@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: Optional[str] = None
    title: str = ""
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 5
    assigned_to: Optional[str] = None
    parent_id: Optional[str] = None
    root_id: Optional[str] = None
    plan: Optional[dict] = None
    result: Optional[dict] = None
    error: Optional[str] = None
    depends_on: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
    score: Optional[float] = None
    tags: list[str] = field(default_factory=list)


class Database:
    """In-memory database with JSON file persistence"""

    def __init__(self, base_dir: str | Path = "."):
        self.base_dir = Path(base_dir)
        self._data_dir = self.base_dir / ".code-swarm" / "db"
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._agents: dict[str, Agent] = {}
        self._sessions: dict[str, Session] = {}
        self._tasks: dict[str, Task] = {}
        self._load()

    def _load(self):
        agents_file = self._data_dir / "agents.json"
        if agents_file.exists():
            data = json.loads(agents_file.read_text())
            self._agents = {k: Agent(**v) for k, v in data.items()}

        sessions_file = self._data_dir / "sessions.json"
        if sessions_file.exists():
            data = json.loads(sessions_file.read_text())
            self._sessions = {k: Session(**v) for k, v in data.items()}

        tasks_file = self._data_dir / "tasks.json"
        if tasks_file.exists():
            data = json.loads(tasks_file.read_text())
            self._tasks = {k: Task(**v) for k, v in data.items()}

    def _save(self):
        (self._data_dir / "agents.json").write_text(
            json.dumps({k: asdict(v) for k, v in self._agents.items()}, indent=2)
        )
        (self._data_dir / "sessions.json").write_text(
            json.dumps({k: asdict(v) for k, v in self._sessions.items()}, indent=2)
        )
        (self._data_dir / "tasks.json").write_text(
            json.dumps({k: asdict(v) for k, v in self._tasks.items()}, indent=2)
        )

    def create_agent(self, name: str, model: str, role: str, **kwargs) -> Agent:
        agent = Agent(name=name, model=model, role=role, **kwargs)
        self._agents[agent.id] = agent
        self._save()
        return agent

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        return self._agents.get(agent_id)

    def list_agents(self, role: Optional[str] = None) -> list[Agent]:
        agents = list(self._agents.values())
        if role:
            agents = [a for a in agents if a.role == role]
        return agents

    def create_session(self, swarm_id: str, **kwargs) -> Session:
        session = Session(swarm_id=swarm_id, **kwargs)
        self._sessions[session.id] = session
        self._save()
        return session

    def create_task(self, title: str, **kwargs) -> Task:
        task = Task(title=title, **kwargs)
        self._tasks[task.id] = task
        self._save()
        return task

    def update_task(self, task_id: str, **kwargs):
        if task_id in self._tasks:
            task = self._tasks[task_id]
            for k, v in kwargs.items():
                if hasattr(task, k):
                    setattr(task, k, v)
            self._save()

    def get_metrics(self) -> dict:
        return {
            "total_agents": len(self._agents),
            "active_sessions": sum(1 for s in self._sessions.values() if s.status == "active"),
            "total_tasks": len(self._tasks),
            "completed_tasks": sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED.value),
            "failed_tasks": sum(1 for t in self._tasks.values() if t.status == TaskStatus.FAILED.value),
        }


def asdict(obj):
    if hasattr(obj, "__dataclass_fields__"):
        result = {}
        for field_name in obj.__dataclass_fields__:
            value = getattr(obj, field_name)
            if isinstance(value, datetime):
                result[field_name] = value.isoformat()
            elif isinstance(value, Enum):
                result[field_name] = value.value
            else:
                result[field_name] = value
        return result
    raise TypeError(f"Cannot convert {type(obj)} to dict")