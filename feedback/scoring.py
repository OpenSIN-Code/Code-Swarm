"""RLHF scoring pipeline for agent output quality."""
import json
import time
from typing import Any

class ScoringPipeline:
    def __init__(self, db_url: str | None = None):
        self.db_url = db_url

    def score_response(self, agent: str, task: str, output: str, feedback: int) -> dict[str, Any]:
        """Score an agent response with human feedback (1-5)."""
        return {
            "agent": agent,
            "task": task,
            "timestamp": time.time(),
            "feedback": max(1, min(5, feedback)),
            "output_length": len(output),
            "score": feedback / 5.0,
        }

    def compute_agent_score(self, scores: list[dict]) -> float:
        if not scores:
            return 0.0
        return sum(s["score"] for s in scores) / len(scores)
