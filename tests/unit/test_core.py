import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import Agent, Task, TaskStatus, AgentStatus
from cache.redis import RedisCache
from storage.s3 import S3Storage
from vector.vector_db import VectorDB
from auth.security import AuthManager, RBACManager


class TestDataclasses:
    """Smoke-test the public dataclasses exposed by db.database.

    The Database class itself is async + PostgreSQL-backed, see
    tests/integration/test_database.py for the connection-level tests.
    """

    def test_agent_defaults(self):
        agent = Agent(name="test-agent", model="test-model", role="planner")
        assert agent.name == "test-agent"
        assert agent.status == "idle"
        assert agent.id  # auto-generated UUID
        assert isinstance(agent.capabilities, list)

    def test_task_defaults(self):
        task = Task(title="Test Task", priority=3)
        assert task.title == "Test Task"
        assert task.priority == 3
        assert task.status == "pending"
        assert task.id  # auto-generated UUID

    def test_status_enums(self):
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.COMPLETED.value == "completed"
        assert AgentStatus.IDLE.value == "idle"
        assert AgentStatus.ACTIVE.value == "active"


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
    def test_create_and_authenticate_user(self, tmp_path):
        auth = AuthManager(secret_key="test-secret-key-123", base_dir=tmp_path)
        user = auth.create_user("testuser", "testpassword", role="developer")
        assert user is not None
        authenticated = auth.authenticate("testuser", "testpassword")
        assert authenticated is not None

    def test_create_and_verify_token(self, tmp_path):
        auth = AuthManager(secret_key="test-secret-key-456", base_dir=tmp_path)
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
