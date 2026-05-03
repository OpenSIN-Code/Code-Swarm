import pytest
import sys
from pathlib import Path
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import Database
from cache.redis import RedisCache
from storage.s3 import S3Storage
from monitoring.metrics import MetricsCollector, HealthChecker


class TestDatabaseIntegration:
    @pytest.mark.asyncio
    async def test_agent_workflow(self, memory_database):
        db = memory_database
        agent = await db.create_agent(name="integration-test", model="test-model", role="planner")

        assert agent.id is not None
        assert agent.name == "integration-test"

        found = await db.get_agent(agent.id)
        assert found.name == "integration-test"
        assert found.role == "planner"

        agents = await db.list_agents()
        assert len(agents) == 1

        agents_by_role = await db.list_agents(role="planner")
        assert len(agents_by_role) == 1

    @pytest.mark.asyncio
    async def test_memory_roundtrip(self, memory_database):
        db = memory_database
        agent = await db.create_agent(name="memory-agent", model="test-model", role="planner")

        await db.store_memory(agent.id, "summary", "hello world", tags=["integration"])
        matches = await db.search_memory("hello")

        assert matches
        assert matches[0]["key"] == "summary"
        assert matches[0]["value"] == "hello world"

        await db.log_event("session-1", agent.id, "agent", "started", data={"agent": agent.id})

    @pytest.mark.asyncio
    async def test_task_workflow(self, memory_database):
        db = memory_database
        agent = await db.create_agent(name="task-agent", model="test-model", role="planner")
        task = await db.create_task(title="integration-task", description="test", priority=7, assigned_to=agent.id)

        assert task.title == "integration-task"

        updated = await db.update_task(task.id, status="completed", duration_ms=120)
        assert updated.status == "completed"

        metrics = await db.get_metrics()
        assert metrics["total_tasks"] == 1
        assert metrics["completed_tasks"] == 1
        assert metrics["avg_task_duration_ms"] == 120


class TestCacheIntegration:
    def test_cache_operations(self):
        temp_dir = tempfile.mkdtemp(prefix="test-cache-")
        try:
            cache = RedisCache(base_dir=temp_dir)
            cache.set("test-key", "test-value")
            value = cache.get("test-key")
            assert value == "test-value"

            cache.delete("test-key")
            deleted = cache.get("test-key")
            assert deleted is None
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestStorageIntegration:
    def test_storage_operations(self):
        temp_dir = tempfile.mkdtemp(prefix="test-s3-")
        try:
            storage = S3Storage(base_dir=temp_dir)
            result = storage.upload("test-file.txt", b"test content")
            assert result["key"] == "test-file.txt"

            content = storage.download("test-file.txt")
            assert content == b"test content"

            storage.delete("test-file.txt")
            deleted = storage.download("test-file.txt")
            assert deleted is None
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestMetricsIntegration:
    def test_metrics_collection(self):
        metrics = MetricsCollector()
        metrics.record_task("test-agent", "completed", 0.5)
        metrics.record_task("test-agent", "failed", 0.3)

        result = metrics.get_metrics()
        assert isinstance(result, str)
        assert "code_swarm_tasks_total" in result
        assert "code_swarm_task_duration_seconds" in result

    def test_health_checker(self):
        temp_dir = tempfile.mkdtemp(prefix="test-health-")
        try:
            health = HealthChecker(base_dir=temp_dir)
            health.check("database", "healthy")
            health.check("cache", "healthy")

            assert health.is_healthy() is True
            status = health.get_status()
            assert status["healthy"] is True
            assert len(status["components"]) == 2
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
