"""Error analysis for self-improvement loops."""
import json
import time
from collections import Counter
from typing import Any


class ErrorAnalyzer:
    def __init__(self):
        self.errors: list[dict[str, Any]] = []

    def record(self, agent: str, error_type: str, context: str) -> None:
        self.errors.append({
            "agent": agent,
            "error_type": error_type,
            "context": context[:200],
            "timestamp": time.time(),
        })

    def top_errors(self, agent: str | None = None, limit: int = 5) -> list[tuple[str, int]]:
        filtered = self.errors
        if agent:
            filtered = [e for e in self.errors if e["agent"] == agent]
        counts = Counter(e["error_type"] for e in filtered)
        return counts.most_common(limit)

    def summary(self) -> dict[str, Any]:
        return {
            "total_errors": len(self.errors),
            "unique_agents": len(set(e["agent"] for e in self.errors)),
            "top_global": self.top_errors(),
        }
