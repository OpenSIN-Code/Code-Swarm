import pytest
import sys
from pathlib import Path
import tempfile
import shutil
import time
import asyncio

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import Database
from cache.redis import RedisCache


class TestEndToEndWorkflow:
    @pytest.mark.asyncio
    async def test_full_agent_task_lifecycle(self, memory_database):
        temp_dir = tempfile.mkdtemp(prefix="test-e2e-")
        try:
            db = memory_database
            cache = RedisCache(base_dir=temp_dir)

            agent = await db.create_agent(name="e2e-agent", model="test-model", role="planner")
            assert agent.id is not None

            task = await db.create_task(title="e2e-task", description="End-to-end test", priority=7, assigned_to=agent.id)
            assert task.id is not None

            cache.set(f"agent:{agent.id}:status", "working")
            status = cache.get(f"agent:{agent.id}:status")
            assert status == "working"

            await db.update_task(task.id, status="completed")

            metrics = await db.get_metrics()
            assert metrics["total_agents"] == 1
            assert metrics["total_tasks"] == 1
            assert metrics["completed_tasks"] == 1
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_multi_agent_coordination(self, memory_database):
        db = memory_database

        agents = []
        for i in range(3):
            agent = await db.create_agent(name=f"coord-agent-{i}", model="test-model", role="worker")
            agents.append(agent)

        task = await db.create_task(title="coord-task", description="Multi-agent task", priority=6)
        assert task.id is not None

        all_agents = await db.list_agents()
        assert len(all_agents) == 3

        workers = await db.list_agents(role="worker")
        assert len(workers) == 3

    @pytest.mark.asyncio
    async def test_database_concurrent_writes(self, memory_database):
        db = memory_database
        num_operations = 100

        start_time = time.perf_counter()
        await asyncio.gather(
            *(db.create_agent(name=f"load-agent-{i}", model="test-model", role="worker") for i in range(num_operations))
        )
        end_time = time.perf_counter()

        duration = end_time - start_time
        ops_per_second = num_operations / duration
        assert ops_per_second > 10, f"Database write performance too slow: {ops_per_second:.2f} ops/sec"

        metrics = await db.get_metrics()
        assert metrics["total_agents"] == num_operations

    def test_cache_concurrent_reads(self):
        temp_dir = tempfile.mkdtemp(prefix="test-load-")
        try:
            cache = RedisCache(base_dir=temp_dir)
            num_operations = 1000

            cache.set("load-test-key", "test-value")

            start_time = time.perf_counter()
            for _ in range(num_operations):
                cache.get("load-test-key")
            end_time = time.perf_counter()

            duration = end_time - start_time
            ops_per_second = num_operations / duration
            assert ops_per_second > 100, f"Cache read performance too slow: {ops_per_second:.2f} ops/sec"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_concurrent_agent_creation(self, memory_database):
        db = memory_database
        num_agents = 50

        async def create_agent(i):
            return await db.create_agent(name=f"concurrent-agent-{i}", model="test-model", role="worker")

        start_time = time.perf_counter()
        results = await asyncio.gather(*(create_agent(i) for i in range(num_agents)))
        end_time = time.perf_counter()

        assert len(results) == num_agents
        duration = end_time - start_time
        assert duration < 30, f"Concurrent agent creation too slow: {duration:.2f}s"
