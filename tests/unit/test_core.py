import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import Database, Agent, Session, Task, TaskStatus, AgentStatus
from cache.redis import RedisCache
from storage.s3 import S3Storage
from vector.vector_db import VectorDB
from auth.security import AuthManager, RBACManager


class TestDatabase:
    def test_create_agent(self):
        db = Database(base_dir="/tmp/test-code-swarm-db")
        agent = db.create_agent(name="test-agent", model="test-model", role="planner")
        assert agent.name == "test-agent"
        assert agent.model == "test-model"
        assert agent.role == "planner"

    def test_get_agent(self):
        db = Database(base_dir="/tmp/test-code-swarm-db2")
        agent = db.create_agent(name="test-agent-2", model="test-model", role="executor")
        found = db.get_agent(agent.id)
        assert found is not None
        assert found.name == "test-agent-2"

    def test_create_session(self):
        db = Database(base_dir="/tmp/test-code-swarm-db3")
        session = db.create_session(swarm_id="test-swarm")
        assert session.swarm_id == "test-swarm"
        assert session.status == "active"

    def test_create_task(self):
        db = Database(base_dir="/tmp/test-code-swarm-db4")
        task = db.create_task(title="Test Task", priority=3)
        assert task.title == "Test Task"
        assert task.priority == 3
        assert task.status == TaskStatus.PENDING

    def test_get_metrics(self):
        db = Database(base_dir="/tmp/test-code-swarm-db5")
        db.create_agent(name="agent-1", model="m1", role="planner")
        db.create_session(swarm_id="swarm-1")
        metrics = db.get_metrics()
        assert metrics["total_agents"] >= 1
        assert metrics["active_sessions"] >= 1


class TestRedisCache:
    def test_set_and_get(self):
        cache = RedisCache(base_dir="/tmp/test-code-swarm-cache")
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_ttl_expiry(self):
        cache = RedisCache(base_dir="/tmp/test-code-swarm-cache2", ttl_seconds=1)
        cache.set("key2", "value2", ttl=1)
        import time
        time.sleep(2)
        assert cache.get("key2") is None

    def test_delete(self):
        cache = RedisCache(base_dir="/tmp/test-code-swarm-cache3")
        cache.set("key3", "value3")
        cache.delete("key3")
        assert cache.get("key3") is None

    def test_stats(self):
        cache = RedisCache(base_dir="/tmp/test-code-swarm-cache4")
        cache.set("a", "1")
        cache.set("b", "2")
        cache.get("a")
        cache.get("a")
        stats = cache.stats()
        assert stats["total_keys"] == 2


class TestS3Storage:
    def test_upload_download(self):
        storage = S3Storage(base_dir="/tmp/test-code-swarm-storage")
        entry = storage.upload("test/file.txt", b"Hello World", mime_type="text/plain")
        assert entry["size_bytes"] == 11
        content = storage.download("test/file.txt")
        assert content == b"Hello World"

    def test_delete(self):
        storage = S3Storage(base_dir="/tmp/test-code-swarm-storage2")
        storage.upload("test/delete.txt", b"Delete me")
        storage.delete("test/delete.txt")
        assert storage.download("test/delete.txt") is None

    def test_list(self):
        storage = S3Storage(base_dir="/tmp/test-code-swarm-storage3")
        storage.upload("folder/file1.txt", b"1")
        storage.upload("folder/file2.txt", b"2")
        storage.upload("other/file3.txt", b"3")
        files = storage.list("folder/")
        assert len(files) == 2


class TestVectorDB:
    def test_insert_search(self):
        vdb = VectorDB(base_dir="/tmp/test-code-swarm-vector")
        vdb.insert("key1", [1.0, 0.0, 0.0], metadata={"text": "hello"})
        vdb.insert("key2", [0.0, 1.0, 0.0], metadata={"text": "world"})
        results = vdb.search([1.0, 0.0, 0.0], top_k=1)
        assert results[0]["key"] == "key1"
        assert results[0]["similarity"] > 0.99

    def test_delete(self):
        vdb = VectorDB(base_dir="/tmp/test-code-swarm-vector2")
        vdb.insert("key1", [1.0, 0.0, 0.0])
        vdb.delete("key1")
        assert vdb.count() == 0


class TestAuthManager:
    def test_create_and_authenticate_user(self):
        auth = AuthManager(secret_key="test-secret-key-123")
        user = auth.create_user("testuser", "testpassword", role="developer")
        assert user is not None
        authenticated = auth.authenticate("testuser", "testpassword")
        assert authenticated is not None

    def test_create_and_verify_token(self):
        auth = AuthManager(secret_key="test-secret-key-456")
        auth.create_user("tokenuser", "password", role="developer")
        token = auth.create_access_token({"sub": "tokenuser"})
        payload = auth.verify_token(token)
        assert payload is not None
        assert payload["sub"] == "tokenuser"


class TestRBACManager:
    def test_has_permission(self):
        rbac = RBACManager()
        assert rbac.has_permission("admin", "read")
        assert rbac.has_permission("developer", "execute")
        assert not rbac.has_permission("viewer", "write")

    def test_grant_revoke(self):
        rbac = RBACManager()
        rbac.grant_permission("viewer", "write")
        assert rbac.has_permission("viewer", "write")
        rbac.revoke_permission("viewer", "write")
        assert not rbac.has_permission("viewer", "write")