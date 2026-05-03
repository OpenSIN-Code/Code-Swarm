from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid
import numpy as np


@dataclass
class FeedbackEntry:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    agent_id: str = ""
    rating: float = 0.0
    content: str = ""
    model_id: str = ""
    feedback_type: str = "human"
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BayesianOptimizer:
    def __init__(self, base_dir: str | Path = "."):
        self.base_dir = Path(base_dir)
        self._feedback_dir = self.base_dir / ".code-swarm" / "feedback"
        self._feedback_dir.mkdir(parents=True, exist_ok=True)
        self._feedback_file = self._feedback_dir / "feedback.json"
        self._entries: list[FeedbackEntry] = []
        self._load()

    def _load(self):
        if self._feedback_file.exists():
            data = json.loads(self._feedback_file.read_text())
            self._entries = [FeedbackEntry(**e) for e in data]

    def _save(self):
        self._feedback_file.write_text(
            json.dumps([vars(e) for e in self._entries], indent=2)
        )

    def add_feedback(
        self,
        task_id: str,
        agent_id: str,
        rating: float,
        content: str,
        model_id: str = "",
        feedback_type: str = "human",
    ) -> FeedbackEntry:
        entry = FeedbackEntry(
            task_id=task_id,
            agent_id=agent_id,
            rating=rating,
            content=content,
            model_id=model_id,
            feedback_type=feedback_type,
        )
        self._entries.append(entry)
        self._save()
        self._optimize_prompts(agent_id)
        return entry

    def _optimize_prompts(self, agent_id: str):
        agent_entries = [e for e in self._entries if e.agent_id == agent_id]
        if len(agent_entries) < 5:
            return
        
        high_rated = [e for e in agent_entries if e.rating >= 0.8]
        low_rated = [e for e in agent_entries if e.rating < 0.5]
        
        if high_rated and low_rated:
            insights = {
                "avg_rating": np.mean([e.rating for e in agent_entries]),
                "high_count": len(high_rated),
                "low_count": len(low_rated),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            insights_file = self._feedback_dir / f"{agent_id}_insights.json"
            insights_file.write_text(json.dumps(insights, indent=2))

    def get_agent_score(self, agent_id: str) -> Optional[float]:
        agent_entries = [e for e in self._entries if e.agent_id == agent_id]
        if not agent_entries:
            return None
        return np.mean([e.rating for e in agent_entries])

    def get_top_performers(self, limit: int = 5) -> list[dict]:
        agent_scores = {}
        for entry in self._entries:
            if entry.agent_id not in agent_scores:
                agent_scores[entry.agent_id] = []
            agent_scores[entry.agent_id].append(entry.rating)
        
        results = []
        for agent_id, ratings in agent_scores.items():
            results.append({
                "agent_id": agent_id,
                "avg_score": np.mean(ratings),
                "sample_count": len(ratings),
            })
        
        results.sort(key=lambda x: x["avg_score"], reverse=True)
        return results[:limit]


class SelfImprover:
    def __init__(self, base_dir: str | Path = "."):
        self.base_dir = Path(base_dir)
        self._improvements_dir = self.base_dir / ".code-swarm" / "improvements"
        self._improvements_dir.mkdir(parents=True, exist_ok=True)
        self.optimizer = BayesianOptimizer(base_dir)

    def suggest_improvement(self, agent_id: str) -> Optional[dict]:
        score = self.optimizer.get_agent_score(agent_id)
        if score is None:
            return None
        
        insights_file = self._improvements_dir / f"{agent_id}_suggestions.json"
        
        if score >= 0.9:
            suggestion = {
                "agent_id": agent_id,
                "current_score": score,
                "suggestion": "Performance is excellent. Consider expanding capabilities.",
                "priority": "low",
            }
        elif score >= 0.7:
            suggestion = {
                "agent_id": agent_id,
                "current_score": score,
                "suggestion": "Performance is good. Minor refinements recommended.",
                "priority": "medium",
            }
        else:
            suggestion = {
                "agent_id": agent_id,
                "current_score": score,
                "suggestion": "Performance needs improvement. Review prompt and model settings.",
                "priority": "high",
            }
        
        insights_file.write_text(json.dumps(suggestion, indent=2))
        return suggestion

    def apply_learning(self, agent_id: str, feedback: list[FeedbackEntry]):
        for fb in feedback:
            self.optimizer.add_feedback(
                task_id=fb.task_id,
                agent_id=agent_id,
                rating=fb.rating,
                content=fb.content,
                model_id=fb.model_id,
            )
        return self.suggest_improvement(agent_id)