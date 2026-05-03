import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
import sys
import time
import concurrent.futures

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import Database
from cache.redis import RedisCache


@pytest.mark.e2e
class TestEndToEndWorkflow:
    def test_full_agent_task_lifecycle(self, temp_db_path):
        db = Database(base_dir=temp_db_path)
        cache = RedisCache()
        
        agent = db.create_agent(name="e2e-agent", model="test-model", role="planner")
        assert agent.id is not None
        
        task = db.create_task(title="e2e-task", description="End-to-end test", priority="high")
        db.assign_task_to_agent(task.id, agent.id)
        
        cache.set(f"agent:{agent.id}:status", "working")
        status = cache.get(f"agent:{agent.id}:status")
        assert status == "working"
        
        db.update_task_status(task.id, "in_progress")
        db.update_task_status(task.id, "completed")
        
        final_task = db.get_task(task.id)
        assert final_task.status == "completed"
        assert final_task.assigned_to == agent.id

    def test_multi_agent_coordination(self, temp_db_path):
        db = Database(base_dir=temp_db_path)
        
        agents = []
        for i in range(3):
            agent = db.create_agent(name=f"coord-agent-{i}", model="test-model", role="worker")
            agents.append(agent)
        
        task = db.create_task(title="coord-task", description="Multi-agent task", priority="high")
        
        for agent in agents:
            db.update_agent_status(agent.id, "active")
        
        db.assign_task_to_agent(task.id, agents[0].id)
        db.update_task_status(task.id, "in_progress")
        
        active_agents = [a for a in agents if db.get_agent(a.id).status == "active"]
        assert len(active_agents) == 3


@pytest.mark.load
class TestLoadPerformance:
    def test_database_concurrent_writes(self, temp_db_path):
        db = Database(base_dir=temp_db_path)
        num_operations = 100
        
        start_time = time.time()
        for i in range(num_operations):
            db.create_agent(name=f"load-agent-{i}", model="test-model", role="worker")
        end_time = time.time()
        
        duration = end_time - start_time
        ops_per_second = num_operations / duration
        assert ops_per_second > 10, f"Database write performance too slow: {ops_per_second:.2f} ops/sec"

    def test_cache_concurrent_reads(self):
        cache = RedisCache()
        num_operations = 1000
        
        cache.set("load-test-key", "test-value")
        
        start_time = time.time()
        for i in range(num_operations):
            cache.get("load-test-key")
        end_time = time.time()
        
        duration = end_time - start_time
        ops_per_second = num_operations / duration
        assert ops_per_second > 100, f"Cache read performance too slow: {ops_per_second:.2f} ops/sec"

    def test_concurrent_agent_creation(self, temp_db_path):
        db = Database(base_dir=temp_db_path)
        num_agents = 50
        
        def create_agent(i):
            return db.create_agent(name=f"concurrent-agent-{i}", model="test-model", role="worker")
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_agent, i) for i in range(num_agents)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        end_time = time.time()
        
        assert len(results) == num_agents
        duration = end_time - start_time
        assert duration < 30, f"Concurrent agent creation too slow: {duration:.2f}s"
