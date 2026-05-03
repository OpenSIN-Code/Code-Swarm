import pytest
import sys
from pathlib import Path
import tempfile
import shutil
import concurrent.futures
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import Database
from cache.redis import RedisCache


class TestEndToEndWorkflow:
    def test_full_agent_task_lifecycle(self):
        temp_dir = tempfile.mkdtemp(prefix="test-e2e-")
        try:
            db = Database(base_dir=temp_dir)
            cache = RedisCache(base_dir=temp_dir)
            
            agent = db.create_agent(name="e2e-agent", model="test-model", role="planner")
            assert agent.id is not None
            
            task = db.create_task(title="e2e-task", description="End-to-end test", priority="high")
            assert task.id is not None
            
            cache.set(f"agent:{agent.id}:status", "working")
            status = cache.get(f"agent:{agent.id}:status")
            assert status == "working"
            
            db.update_task(task.id, status="completed")
            
            metrics = db.get_metrics()
            assert metrics["total_agents"] == 1
            assert metrics["total_tasks"] == 1
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_multi_agent_coordination(self):
        temp_dir = tempfile.mkdtemp(prefix="test-e2e-")
        try:
            db = Database(base_dir=temp_dir)
            
            agents = []
            for i in range(3):
                agent = db.create_agent(name=f"coord-agent-{i}", model="test-model", role="worker")
                agents.append(agent)
            
            task = db.create_task(title="coord-task", description="Multi-agent task", priority="high")
            assert task.id is not None
            
            all_agents = db.list_agents()
            assert len(all_agents) == 3
            
            workers = db.list_agents(role="worker")
            assert len(workers) == 3
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestLoadPerformance:
    def test_database_concurrent_writes(self):
        temp_dir = tempfile.mkdtemp(prefix="test-load-")
        try:
            db = Database(base_dir=temp_dir)
            num_operations = 100
            
            start_time = time.time()
            for i in range(num_operations):
                db.create_agent(name=f"load-agent-{i}", model="test-model", role="worker")
            end_time = time.time()
            
            duration = end_time - start_time
            ops_per_second = num_operations / duration
            assert ops_per_second > 10, f"Database write performance too slow: {ops_per_second:.2f} ops/sec"
            
            metrics = db.get_metrics()
            assert metrics["total_agents"] == num_operations
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_cache_concurrent_reads(self):
        temp_dir = tempfile.mkdtemp(prefix="test-load-")
        try:
            cache = RedisCache(base_dir=temp_dir)
            num_operations = 1000
            
            cache.set("load-test-key", "test-value")
            
            start_time = time.time()
            for i in range(num_operations):
                cache.get("load-test-key")
            end_time = time.time()
            
            duration = end_time - start_time
            ops_per_second = num_operations / duration
            assert ops_per_second > 100, f"Cache read performance too slow: {ops_per_second:.2f} ops/sec"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_concurrent_agent_creation(self):
        temp_dir = tempfile.mkdtemp(prefix="test-load-")
        try:
            db = Database(base_dir=temp_dir)
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
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
