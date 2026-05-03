"""Bayesian optimization for agent hyperparameters."""
from __future__ import annotations
import random


class BayesianOptimizer:
    def __init__(self, learning_rate: float = 0.1):
        self.learning_rate = learning_rate
        self.history: list[dict] = []

    def suggest(self, param_ranges: dict[str, tuple[float, float]]) -> dict[str, float]:
        suggestion = {}
        for param, (low, high) in param_ranges.items():
            if self.history:
                best = max(self.history, key=lambda x: x.get("score", 0))
                suggestion[param] = best.get(param, random.uniform(low, high)) * (1 + random.gauss(0, self.learning_rate))
                suggestion[param] = max(low, min(high, suggestion[param]))
            else:
                suggestion[param] = random.uniform(low, high)
        return suggestion

    def update(self, params: dict[str, float], score: float) -> None:
        self.history.append({**params, "score": score})
