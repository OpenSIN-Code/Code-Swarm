from __future__ import annotations
import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid
from enum import Enum
import os
import logging
from contextlib import asynccontextmanager

import asyncpg

logger = logging.getLogger("code-swarm.db")


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
    status: str = "idle"
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_seen_at: Optional[str] = None


@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: Optional[str] = None
    title: str = ""
    description: Optional[str] = None
    status: str = "pending"
    priority: int = 5
    assigned_to: Optional[str] = None
    parent_id: Optional[str] = None
    root_id: Optional[str] = None
    plan: Optional[Dict] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
    score: Optional[float] = None
    tags: List[str] = field(default_factory=list)


class Database:
    """Production PostgreSQL database with async connection pooling."""

    def __init__(self, dsn: Optional[str] = None):
        """Initialize with DSN from environment or parameter."""
        self.dsn = dsn or os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/code_swarm"
        )
        self.pool: Optional[asyncpg.Pool] = None
        self._initialized = False

    async def initialize(self):
        """Initialize connection pool."""
        if self._initialized:
            return

        try:
            self.pool = await asyncpg.create_pool(
                self.dsn,
                min_size=5,
                max_size=20,
                command_timeout=60,
            )
            await self._create_schema()
            self._initialized = True
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    async def _create_schema(self):
        """Create schema if it doesn't exist."""
        async with self.pool.acquire() as conn:
            # Check if agents table exists
            result = await conn.fetchval(
                """SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'agents'
                )"""
            )
            if not result:
                logger.info("Creating database schema...")
                schema_sql = open("db/schema.sql").read()
                await conn.execute(schema_sql)
                logger.info("Schema created")

    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool."""
        if not self.pool:
            await self.initialize()
        async with self.pool.acquire() as conn:
            yield conn

    async def close(self):
        """Close the connection pool."""
        if self.pool:
            await self.pool.close()

    # ====== AGENT OPERATIONS ======

    async def create_agent(
        self,
        name: str,
        model: str,
        role: str,
        capabilities: List[str] = None,
        metadata: Dict = None,
    ) -> Agent:
        """Create a new agent."""
        agent_id = str(uuid.uuid4())
        async with self.get_connection() as conn:
            await conn.execute(
                """INSERT INTO agents (id, name, model, role, capabilities, metadata)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                agent_id,
                name,
                model,
                role,
                capabilities or [],
                metadata or {},
            )
        return Agent(
            id=agent_id,
            name=name,
            model=model,
            role=role,
            capabilities=capabilities or [],
            metadata=metadata or {},
        )

    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        async with self.get_connection() as conn:
            row = await conn.fetchrow("SELECT * FROM agents WHERE id = $1", agent_id)
        if not row:
            return None
        return Agent(**dict(row))

    async def list_agents(self, role: Optional[str] = None) -> List[Agent]:
        """List all agents, optionally filtered by role."""
        async with self.get_connection() as conn:
            if role:
                rows = await conn.fetch("SELECT * FROM agents WHERE role = $1", role)
            else:
                rows = await conn.fetch("SELECT * FROM agents")
        return [Agent(**dict(row)) for row in rows]

    async def update_agent_status(self, agent_id: str, status: str):
        """Update agent status."""
        async with self.get_connection() as conn:
            await conn.execute(
                "UPDATE agents SET status = $1, updated_at = NOW() WHERE id = $2",
                status,
                agent_id,
            )

    # ====== TASK OPERATIONS ======

    async def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        priority: int = 5,
        assigned_to: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Task:
        """Create a new task."""
        task_id = str(uuid.uuid4())
        async with self.get_connection() as conn:
            await conn.execute(
                """INSERT INTO tasks (id, title, description, priority, assigned_to, session_id)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                task_id,
                title,
                description,
                priority,
                assigned_to,
                session_id,
            )
        return Task(
            id=task_id,
            title=title,
            description=description,
            priority=priority,
            assigned_to=assigned_to,
            session_id=session_id,
        )

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        async with self.get_connection() as conn:
            row = await conn.fetchrow("SELECT * FROM tasks WHERE id = $1", task_id)
        if not row:
            return None
        return Task(**dict(row))

    async def list_tasks(
        self,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None,
    ) -> List[Task]:
        """List tasks with optional filters."""
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []

        if status:
            query += " AND status = $" + str(len(params) + 1)
            params.append(status)
        if assigned_to:
            query += " AND assigned_to = $" + str(len(params) + 1)
            params.append(assigned_to)

        async with self.get_connection() as conn:
            rows = await conn.fetch(query, *params)

        return [Task(**dict(row)) for row in rows]

    async def update_task(self, task_id: str, **kwargs) -> Task:
        """Update task fields."""
        allowed_fields = {
            "status", "priority", "assigned_to", "result", "error", 
            "completed_at", "duration_ms", "score"
        }
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not updates:
            return await self.get_task(task_id)

        set_clause = ", ".join(f"{k} = ${i+1}" for i, k in enumerate(updates.keys()))
        query = f"UPDATE tasks SET {set_clause}, updated_at = NOW() WHERE id = ${len(updates)+1}"

        async with self.get_connection() as conn:
            await conn.execute(query, *updates.values(), task_id)

        return await self.get_task(task_id)

    # ====== METRICS ======

    async def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics."""
        async with self.get_connection() as conn:
            metrics = await conn.fetchrow("""
                SELECT
                    (SELECT COUNT(*) FROM agents) AS total_agents,
                    (SELECT COUNT(*) FROM tasks) AS total_tasks,
                    (SELECT COUNT(*) FROM tasks WHERE status = 'completed') AS completed_tasks,
                    (SELECT COUNT(*) FROM tasks WHERE status = 'failed') AS failed_tasks,
                    (SELECT AVG(duration_ms) FROM tasks WHERE duration_ms IS NOT NULL) AS avg_task_duration_ms
            """)

        return {
            "total_agents": metrics["total_agents"],
            "total_tasks": metrics["total_tasks"],
            "completed_tasks": metrics["completed_tasks"],
            "failed_tasks": metrics["failed_tasks"],
            "avg_task_duration_ms": metrics["avg_task_duration_ms"],
        }

    # ====== MEMORY (Vector Search) ======

    async def store_memory(
        self,
        agent_id: str,
        key: str,
        value: str,
        embedding: Optional[List[float]] = None,
        tags: List[str] = None,
    ):
        """Store memory with optional embedding."""
        memory_id = str(uuid.uuid4())
        async with self.get_connection() as conn:
            await conn.execute(
                """INSERT INTO memory (id, agent_id, key, value, embedding, tags)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                memory_id,
                agent_id,
                key,
                value,
                embedding,
                tags or [],
            )

    async def search_memory(self, query: str, limit: int = 10) -> List[Dict]:
        """Search memory by full-text search."""
        async with self.get_connection() as conn:
            rows = await conn.fetch(
                """SELECT id, key, value FROM memory
                   WHERE value ILIKE '%' || $1 || '%'
                   ORDER BY updated_at DESC
                   LIMIT $2""",
                query,
                limit,
            )
        return [dict(row) for row in rows]

    # ====== EVENTS (Audit Log) ======

    async def log_event(
        self,
        session_id: str,
        agent_id: Optional[str],
        event_type: str,
        action: str,
        data: Dict = None,
        trace_id: Optional[str] = None,
    ):
        """Log an event."""
        async with self.get_connection() as conn:
            await conn.execute(
                """INSERT INTO events (session_id, agent_id, type, action, data, trace_id)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                session_id,
                agent_id,
                event_type,
                action,
                data or {},
                trace_id,
            )

    # ====== FEEDBACK (RLHF) ======

    async def store_feedback(
        self,
        task_id: str,
        agent_id: str,
        feedback_type: str,
        rating: Optional[float] = None,
        content: Optional[str] = None,
    ):
        """Store feedback for learning."""
        feedback_id = str(uuid.uuid4())
        async with self.get_connection() as conn:
            await conn.execute(
                """INSERT INTO feedback (id, task_id, agent_id, type, rating, content)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                feedback_id,
                task_id,
                agent_id,
                feedback_type,
                rating,
                content,
            )


# Singleton instance
_db_instance: Optional[Database] = None


def get_database() -> Database:
    """Get or create database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


async def close_database():
    """Close database connection."""
    global _db_instance
    if _db_instance:
        await _db_instance.close()
        _db_instance = None
