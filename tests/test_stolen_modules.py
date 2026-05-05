"""Tests for all 7 stolen code-swarm modules."""

import os
import tempfile
import json
from pathlib import Path

from code_swarm.agent_loop import EventLoop, ToolExecutor, SwarmEvent, EventType
from code_swarm.mcp_hub import MCPHub
from code_swarm.repo_map import RepoMap
from code_swarm.edit_engine import EditEngine, hash_line
from code_swarm.sub_agent import SubAgentPool
from code_swarm.modes import PlanActVerify, AgentMode, ApprovalGate
from code_swarm.checkpointing import Checkpointer


def test_event_loop():
    loop = EventLoop()
    event = SwarmEvent(type=EventType.USER_MESSAGE, agent="zeus", content="hello")
    loop.emit(event)
    assert len(loop.recent()) == 1
    assert loop.recent()[0].content == "hello"
    visible = loop.visible_to_llm()
    assert len(visible) == 1


def test_tool_executor():
    exe = ToolExecutor()
    exe.register("echo", lambda x: x, schema={"type": "object"})
    assert "echo" in exe.list_tools()
    result = exe.execute("echo", x="hello")
    assert result["status"] == "success"
    result2 = exe.execute("nonexistent")
    assert result2["status"] == "error"


def test_mcp_hub():
    hub = MCPHub()
    hub._servers["test-server"] = {"type": "stdio", "enabled": True}
    available = hub.list_available()
    assert len(available) >= 1


def test_repo_map():
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / "test.py"
        p.write_text("def hello():\n    pass\nclass Test:\n    pass\n")
        rm = RepoMap(tmpdir, max_tokens=500)
        tree = rm.build()
        assert "test.py" in tree
        summary = rm.summarize()
        assert "def hello" in summary


def test_edit_engine():
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
        f.write("def old():\n    return 1\n")
        fpath = f.name
    try:
        ee = EditEngine(fpath)
        h = hash_line("def old():\n    return 1\n")
        assert len(h) == 8
        assert ee.replace("old", "new")
        with open(fpath) as f:
            assert "new()" in f.read()
    finally:
        os.unlink(fpath)


def test_sub_agent_pool():
    with tempfile.TemporaryDirectory() as tmpdir:
        pool = SubAgentPool(tmpdir, max_agents=3)
        aid = pool.spawn("test task")
        assert aid.startswith("sub_")
        assert pool.list_active()
        pool.cleanup(aid)
        assert not pool.list_active()


def test_plan_act_verify():
    pav = PlanActVerify()
    assert pav.mode == AgentMode.PLAN
    gate = ApprovalGate(AgentMode.YOLO)
    assert gate.check("delete everything", "high") is True
    gate2 = ApprovalGate(AgentMode.PLAN)
    assert gate2.check("edit file") is False


def test_checkpointer():
    cp = Checkpointer("test_agent")
    cp.save("test_ck", {"step": 1, "data": "hello"})
    loaded = cp.load("test_ck")
    assert loaded and loaded["step"] == 1
    assert cp.load_latest()["step"] == 1
    cks = cp.list_checkpoints()
    assert len(cks) >= 1
    cp.delete("test_ck")
    assert cp.load("test_ck") is None
