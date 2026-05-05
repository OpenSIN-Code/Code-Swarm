"""Code-Swarm: Event-driven agent loop (stolen from OpenHands)

Pattern: immutable event log as single source of truth.
Events are append-only. LLM-visible vs internal events separated.
Strict Action -> Observation contract with type-safe schemas.
"""

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class EventType(Enum):
    USER_MESSAGE = "user_message"
    AGENT_THOUGHT = "agent_thought"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    SYSTEM = "system"
    ERROR = "error"


@dataclass
class SwarmEvent:
    id: str = field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    type: EventType = EventType.SYSTEM
    timestamp: float = field(default_factory=time.time)
    agent: str = ""
    content: str = ""
    metadata: dict = field(default_factory=dict)
    parent_id: Optional[str] = None


class EventLoop:
    """Immutable event log - single source of truth."""

    def __init__(self):
        self._events: list[SwarmEvent] = []
        self._handlers: dict[EventType, list[Callable]] = {}

    def emit(self, event: SwarmEvent) -> SwarmEvent:
        self._events.append(event)
        for handler in self._handlers.get(event.type, []):
            handler(event)
        return event

    def subscribe(self, event_type: EventType, handler: Callable):
        self._handlers.setdefault(event_type, []).append(handler)

    def recent(self, n: int = 20, agent: Optional[str] = None) -> list[SwarmEvent]:
        filtered = [e for e in self._events if agent is None or e.agent == agent]
        return filtered[-n:]

    def visible_to_llm(self, n: int = 50) -> list[dict]:
        """Events the LLM can see - filters internal/system noise."""
        return [
            {"type": e.type.value, "agent": e.agent, "content": e.content[:2000]}
            for e in self._events[-n:]
            if e.type != EventType.SYSTEM
        ]

    def clear(self):
        self._events.clear()


class ToolExecutor:
    """Strict Action -> Observation contract."""

    def __init__(self):
        self._tools: dict[str, Callable] = {}

    def register(self, name: str, fn: Callable, schema: Optional[dict] = None):
        self._tools[name] = fn

    def execute(self, name: str, **kwargs) -> dict:
        if name not in self._tools:
            return {"status": "error", "error": f"Unknown tool: {name}"}
        try:
            result = self._tools[name](**kwargs)
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())
