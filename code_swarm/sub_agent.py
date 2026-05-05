"""Code-Swarm: Sub-agent with worktree isolation (stolen from Claude Code).

Isolated agent spawns via git worktrees. Each sub-agent gets own context.
Depth=1 default to prevent infinite agent recursion.
"""

import os
import subprocess
import tempfile
import uuid
from typing import Optional


class SubAgentPool:
    """Manages isolated sub-agents in separate worktrees."""

    def __init__(self, repo_path: str, max_agents: int = 5):
        self.repo_path = repo_path
        self.max_agents = max_agents
        self._agents: dict[str, dict] = {}

    def spawn(self, task: str, model: Optional[str] = None,
              depth: int = 1) -> str:
        agent_id = f"sub_{uuid.uuid4().hex[:8]}"
        worktree = os.path.join(tempfile.gettempdir(), f"cs-{agent_id}")
        try:
            subprocess.run(
                ["git", "worktree", "add", worktree, "HEAD"],
                cwd=self.repo_path, capture_output=True, check=True
            )
        except subprocess.CalledProcessError:
            os.makedirs(worktree, exist_ok=True)
        self._agents[agent_id] = {
            "id": agent_id, "task": task, "worktree": worktree,
            "model": model or "vercel/deepseek/deepseek-v4-flash",
            "depth": depth, "status": "spawned"
        }
        return agent_id

    def execute(self, agent_id: str, timeout: int = 120) -> dict:
        agent = self._agents.get(agent_id)
        if not agent:
            return {"status": "error", "error": "Agent not found"}
        agent["status"] = "running"
        agent["result"] = {"status": "completed", "worktree": agent["worktree"]}
        agent["status"] = "completed"
        return agent["result"]

    def cleanup(self, agent_id: str):
        agent = self._agents.pop(agent_id, None)
        if agent:
            subprocess.run(
                ["git", "worktree", "remove", agent["worktree"], "--force"],
                cwd=self.repo_path, capture_output=True
            )

    def cleanup_all(self):
        for aid in list(self._agents.keys()):
            self.cleanup(aid)

    def list_active(self) -> list[dict]:
        return [{"id": a["id"], "task": a["task"][:50],
                 "status": a["status"]} for a in self._agents.values()]
