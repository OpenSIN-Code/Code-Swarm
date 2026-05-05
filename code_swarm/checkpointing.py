"""Code-Swarm: Durable checkpointed state (stolen from LangGraph).

Persistence layer with crash recovery. State survives process restarts.
"""

import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional


_CHECKPOINT_DIR = Path.home() / ".code-swarm" / "checkpoints"
_CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
_DB_PATH = _CHECKPOINT_DIR / "state.db"


def _get_db():
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS checkpoints (
            id TEXT PRIMARY KEY,
            state TEXT NOT NULL,
            created_at REAL NOT NULL,
            agent TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            checkpoint_id TEXT NOT NULL,
            type TEXT NOT NULL,
            data TEXT NOT NULL,
            timestamp REAL NOT NULL,
            FOREIGN KEY (checkpoint_id) REFERENCES checkpoints(id)
        )
    """)
    conn.commit()
    return conn


class Checkpointer:
    """Durable execution state - survives crashes."""

    def __init__(self, agent: str = "default"):
        self.agent = agent
        self._conn = _get_db()

    def save(self, checkpoint_id: str, state: dict) -> bool:
        self._conn.execute(
            "INSERT OR REPLACE INTO checkpoints VALUES (?, ?, ?, ?)",
            (checkpoint_id, json.dumps(state), time.time(), self.agent)
        )
        self._conn.commit()
        return True

    def load(self, checkpoint_id: str) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT state FROM checkpoints WHERE id = ?", (checkpoint_id,)
        ).fetchone()
        return json.loads(row[0]) if row else None

    def load_latest(self) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT state FROM checkpoints WHERE agent = ? ORDER BY created_at DESC LIMIT 1",
            (self.agent,)
        ).fetchone()
        return json.loads(row[0]) if row else None

    def list_checkpoints(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT id, created_at, agent FROM checkpoints WHERE agent = ? ORDER BY created_at DESC",
            (self.agent,)
        ).fetchall()
        return [{"id": r[0], "created": r[1], "agent": r[2]} for r in rows]

    def delete(self, checkpoint_id: str):
        self._conn.execute("DELETE FROM checkpoints WHERE id = ?", (checkpoint_id,))
        self._conn.execute("DELETE FROM events WHERE checkpoint_id = ?", (checkpoint_id,))
        self._conn.commit()


class StatefulAgent:
    """Agent wrapper with automatic checkpoint/restore."""

    def __init__(self, agent_id: str, state: Optional[dict] = None):
        self.agent_id = agent_id
        self.checkpointer = Checkpointer(agent_id)
        self.state = state or self.checkpointer.load_latest() or {}

    def run(self, task: str, executor) -> dict:
        try:
            checkpoint_id = f"ck_{self.agent_id}_{int(time.time())}"
            self.state["task"] = task
            result = executor(self.state, task)
            self.state["last_result"] = str(result)[:500]
            self.checkpointer.save(checkpoint_id, self.state)
            return result
        except Exception as e:
            restored = self.checkpointer.load_latest()
            if restored:
                self.state = restored
                return self.run(task, executor)
            return {"status": "error", "error": str(e)}
