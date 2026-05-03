import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path


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
