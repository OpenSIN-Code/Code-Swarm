from __future__ import annotations
import time
import json
from pathlib import Path
from typing import Optional
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource


class MetricsCollector:
    def __init__(self, service_name: str = "code-swarm"):
        self.service_name = service_name
        self.registry = CollectorRegistry()
        
        self.tasks_total = Counter(
            "code_swarm_tasks_total", "Total tasks processed",
            ["status", "agent"], registry=self.registry
        )
        self.task_duration = Histogram(
            "code_swarm_task_duration_seconds", "Task duration in seconds",
            ["agent", "task_type"], registry=self.registry
        )
        self.agents_active = Gauge(
            "code_swarm_agents_active", "Number of active agents",
            ["agent"], registry=self.registry
        )
        self.sessions_active = Gauge(
            "code_swarm_sessions_active", "Number of active sessions",
            registry=self.registry
        )
        self.error_count = Counter(
            "code_swarm_errors_total", "Total errors",
            ["agent", "error_type"], registry=self.registry
        )
        
        self._setup_tracing()

    def _setup_tracing(self):
        resource = Resource.create({"service.name": self.service_name})
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)

    def record_task(self, agent: str, status: str, duration: float, task_type: str = "default"):
        self.tasks_total.labels(agent=agent, status=status).inc()
        self.task_duration.labels(agent=agent, task_type=task_type).observe(duration)

    def set_active_agents(self, agents: list[str]):
        for agent in agents:
            self.agents_active.labels(agent=agent).set(1)

    def set_active_sessions(self, count: int):
        self.sessions_active.set(count)

    def record_error(self, agent: str, error_type: str):
        self.error_count.labels(agent=agent, error_type=error_type).inc()

    def get_metrics(self) -> str:
        return generate_latest(self.registry).decode("utf-8")


class HealthChecker:
    def __init__(self, base_dir: str | Path = "."):
        self.base_dir = Path(base_dir)
        self._health_file = self.base_dir / ".code-swarm" / "health.json"
        self._checks: dict[str, dict] = {}

    def check(self, component: str, status: str, details: Optional[dict] = None):
        self._checks[component] = {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {},
        }
        self._save()

    def _save(self):
        self._health_file.parent.mkdir(parents=True, exist_ok=True)
        self._health_file.write_text(json.dumps(self._checks, indent=2))

    def is_healthy(self) -> bool:
        return all(c.get("status") == "healthy" for c in self._checks.values())

    def get_status(self) -> dict:
        return {
            "healthy": self.is_healthy(),
            "components": self._checks,
        }