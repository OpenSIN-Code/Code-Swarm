import pytest
import sys
from pathlib import Path
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import Database
from cache.redis import RedisCache
from storage.s3 import S3Storage
from monitoring.metrics import MetricsCollector


class TestDatabaseIntegration:
    def test_agent_lifecycle(self):
        temp_dir = tempfile.mkdtemp(prefix="test-db-")
        try:
            db = Database(base_dir=temp_dir)
            agent = db.create_agent(name="integration-test", model="test-model", role="planner")
            assert agent.id is not None
            
            found = db.get_agent(agent.id)
            assert found.name == "integration-test"
            
            db.update_agent_status(agent.id, "active")
            updated = db.get_agent(agent.id)
            assert updated.status == "active"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_session_persistence(self):
        temp_dir = tempfile.mkdtemp(prefix="test-db-")
        try:
            db = Database(base_dir=temp_dir)
            session = db.create_session(agent_id="test-agent", context={"test": "data"})
            assert session.id is not None
            
            found = db.get_session(session.id)
            assert found.context["test"] == "data"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


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
            storage = S3Storage(bucket_path=temp_dir)
            storage.upload("test-file.txt", b"test content")
            
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
        metrics.record("request_duration", 0.5)
        metrics.record("request_duration", 0.3)
        metrics.record("request_duration", 0.7)
        
        stats = metrics.get_stats("request_duration")
        assert stats["count"] == 3
        assert stats["min"] == 0.3
        assert stats["max"] == 0.7
