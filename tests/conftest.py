import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from copy import deepcopy
from datetime import datetime, timezone


@pytest.fixture
async def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_db_path():
    """Create a temporary directory for database tests."""
    temp_dir = tempfile.mkdtemp(prefix="test-code-swarm-")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_s3_bucket():
    """Create a temporary S3 bucket path for tests."""
    temp_dir = tempfile.mkdtemp(prefix="test-s3-bucket-")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_redis():
    """Mock Redis connection for tests."""
    class MockRedis:
        def __init__(self):
            self.data = {}
        
        async def get(self, key):
            return self.data.get(key)
        
        async def set(self, key, value, expire=None):
            self.data[key] = value
        
        async def delete(self, key):
            if key in self.data:
                del self.data[key]
    
    return MockRedis()


@pytest.fixture
def sample_agent_config():
    """Sample agent configuration for tests."""
    return {
        "name": "test-agent",
        "model": "vercel/deepseek-v4-flash",
        "role": "planner",
        "capabilities": ["coding", "review"],
        "max_tokens": 4096
    }


@pytest.fixture
def sample_task_config():
    """Sample task configuration for tests."""
    return {
        "title": "test-task",
        "description": "Test task for unit testing",
        "status": "pending",
        "priority": "high"
    }


class _FakeDatabaseStore:
    def __init__(self):
        self.agents: dict[str, dict] = {}
        self.tasks: dict[str, dict] = {}
        self.memory: dict[str, dict] = {}
        self.events: list[dict] = []
        self.feedback: dict[str, dict] = {}


class _FakeAcquireContext:
    def __init__(self, connection):
        self._connection = connection

    async def __aenter__(self):
        return self._connection

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeDatabaseConnection:
    def __init__(self, store: _FakeDatabaseStore):
        self.store = store

    async def fetchval(self, query, *args):
        if "information_schema.tables" in query:
            return True
        return None

    async def execute(self, query, *args):
        now = datetime.now(timezone.utc).isoformat()

        if query.startswith("INSERT INTO agents"):
            agent_id, name, model, role, capabilities, metadata = args
            self.store.agents[agent_id] = {
                "id": agent_id,
                "name": name,
                "model": model,
                "fallback_model": None,
                "role": role,
                "status": "idle",
                "capabilities": list(capabilities or []),
                "metadata": deepcopy(metadata or {}),
                "created_at": now,
                "updated_at": now,
                "last_seen_at": None,
            }
            return "INSERT 0 1"

        if query.startswith("UPDATE agents SET status"):
            status, agent_id = args
            record = self.store.agents[agent_id]
            record["status"] = status
            record["updated_at"] = now
            return "UPDATE 1"

        if query.startswith("INSERT INTO tasks"):
            task_id, title, description, priority, assigned_to, session_id = args
            self.store.tasks[task_id] = {
                "id": task_id,
                "session_id": session_id,
                "title": title,
                "description": description,
                "status": "pending",
                "priority": priority,
                "assigned_to": assigned_to,
                "parent_id": None,
                "root_id": None,
                "plan": None,
                "result": None,
                "error": None,
                "depends_on": [],
                "created_at": now,
                "started_at": None,
                "completed_at": None,
                "duration_ms": None,
                "score": None,
                "tags": [],
            }
            return "INSERT 0 1"

        if query.startswith("UPDATE tasks SET"):
            task_id = args[-1]
            values = args[:-1]
            set_clause = query.split("SET", 1)[1].split("WHERE", 1)[0]
            fields = []
            for segment in set_clause.split(","):
                field = segment.split("=", 1)[0].strip()
                if field != "updated_at":
                    fields.append(field)

            record = self.store.tasks[task_id]
            for field, value in zip(fields, values):
                record[field] = value
            return "UPDATE 1"

        if query.startswith("INSERT INTO memory"):
            memory_id, agent_id, key, value, embedding, tags = args
            self.store.memory[memory_id] = {
                "id": memory_id,
                "agent_id": agent_id,
                "key": key,
                "value": value,
                "embedding": embedding,
                "tags": list(tags or []),
                "created_at": now,
                "updated_at": now,
            }
            return "INSERT 0 1"

        if query.startswith("INSERT INTO events"):
            session_id, agent_id, event_type, action, data, trace_id = args
            self.store.events.append(
                {
                    "session_id": session_id,
                    "agent_id": agent_id,
                    "type": event_type,
                    "action": action,
                    "data": deepcopy(data or {}),
                    "trace_id": trace_id,
                    "created_at": now,
                }
            )
            return "INSERT 0 1"

        if query.startswith("INSERT INTO feedback"):
            feedback_id, task_id, agent_id, feedback_type, rating, content = args
            self.store.feedback[feedback_id] = {
                "id": feedback_id,
                "task_id": task_id,
                "agent_id": agent_id,
                "type": feedback_type,
                "rating": rating,
                "content": content,
                "created_at": now,
            }
            return "INSERT 0 1"

        return "OK"

    async def fetchrow(self, query, *args):
        if "FROM agents WHERE id = $1" in query:
            record = self.store.agents.get(args[0])
            return deepcopy(record) if record else None

        if "FROM tasks WHERE id = $1" in query:
            record = self.store.tasks.get(args[0])
            return deepcopy(record) if record else None

        if "SELECT" in query and "total_agents" in query:
            total_agents = len(self.store.agents)
            total_tasks = len(self.store.tasks)
            completed_tasks = sum(1 for task in self.store.tasks.values() if task["status"] == "completed")
            failed_tasks = sum(1 for task in self.store.tasks.values() if task["status"] == "failed")
            durations = [task["duration_ms"] for task in self.store.tasks.values() if task["duration_ms"] is not None]
            avg_task_duration_ms = sum(durations) / len(durations) if durations else None
            return {
                "total_agents": total_agents,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "avg_task_duration_ms": avg_task_duration_ms,
            }

        return None

    async def fetch(self, query, *args):
        if "FROM agents" in query:
            rows = list(self.store.agents.values())
            if "WHERE role = $1" in query:
                role = args[0]
                rows = [row for row in rows if row["role"] == role]
            return [deepcopy(row) for row in rows]

        if "FROM tasks" in query:
            rows = list(self.store.tasks.values())
            if "status = $" in query:
                status = args[0]
                rows = [row for row in rows if row["status"] == status]
            if "assigned_to = $" in query:
                assigned_to = args[1] if len(args) > 1 else args[0]
                rows = [row for row in rows if row["assigned_to"] == assigned_to]
            return [deepcopy(row) for row in rows]

        if "FROM memory" in query:
            term, limit = args
            rows = [
                deepcopy(row)
                for row in reversed(list(self.store.memory.values()))
                if term.lower() in row["value"].lower()
            ]
            return rows[:limit]

        return []


class _FakeDatabasePool:
    def __init__(self, store: _FakeDatabaseStore):
        self._store = store

    def acquire(self):
        return _FakeAcquireContext(_FakeDatabaseConnection(self._store))

    async def close(self):
        return None


@pytest.fixture
def memory_database(monkeypatch):
    """Provide a Database instance backed by an in-memory asyncpg stub."""
    from db import database as db_module
    from db.database import Database

    store = _FakeDatabaseStore()

    async def fake_create_pool(*args, **kwargs):
        return _FakeDatabasePool(store)

    monkeypatch.setattr(db_module.asyncpg, "create_pool", fake_create_pool)
    return Database(dsn="postgresql://memory")
