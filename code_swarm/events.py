"""
Event Sourcing — Append-only Event Log für Agenten-Aktionen
Portiert aus Plugin-SIN-Swarm plugins/state.ts (SOTA)
Ermöglicht Audit Trail, Debugging und Analyse

KEIN tmux, KEINE Worktrees — reine Event-Log-Dateien (.jsonl)
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class SwarmEvent:
    """Ein Event im Agenten-System"""
    id: str = field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    type: str = ""
    swarm_id: str = "code-swarm"
    agent_id: str = ""
    session_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    data: dict = field(default_factory=dict)


def _events_dir(base_dir: str | Path = ".") -> Path:
    path = Path(base_dir) / ".code-swarm" / "events"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _events_file(base_dir: str | Path = ".") -> Path:
    return _events_dir(base_dir) / "events.jsonl"


def append_event(
    event_type: str,
    agent_id: str = "",
    swarm_id: str = "code-swarm",
    session_id: Optional[str] = None,
    data: dict | None = None,
    base_dir: str | Path = ".",
) -> SwarmEvent:
    """
    Hänge ein Event an das Append-only Event Log an.
    
    Args:
        event_type: Typ des Events (z.B. "task.started", "agent.completed")
        agent_id: ID des Agenten
        swarm_id: ID des Swarms
        session_id: Optionale Session-ID
        data: Zusätzliche Daten
        base_dir: Basis-Verzeichnis für .code-swarm/events/
    
    Returns:
        Das erstellte Event
    
    Example:
        >>> append_event("agent.started", "athena", data={"task": "Research"})
    """
    event = SwarmEvent(
        type=event_type,
        swarm_id=swarm_id,
        agent_id=agent_id,
        session_id=session_id,
        data=data or {},
    )
    
    filepath = _events_file(base_dir)
    with open(filepath, "a") as f:
        f.write(json.dumps({
            "id": event.id,
            "type": event.type,
            "swarm_id": event.swarm_id,
            "agent_id": event.agent_id,
            "session_id": event.session_id,
            "timestamp": event.timestamp,
            "data": event.data,
        }) + "\n")
    
    return event


def load_events(
    swarm_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 100,
    base_dir: str | Path = ".",
) -> list[SwarmEvent]:
    """
    Lade Events aus dem Append-only Log.
    
    Args:
        swarm_id: Optional filter nach swarm_id
        agent_id: Optional filter nach agent_id
        event_type: Optional filter nach event_type
        limit: Maximale Anzahl Events
        base_dir: Basis-Verzeichnis
    
    Returns:
        Liste der gefilterten Events (neueste zuerst)
    """
    filepath = _events_file(base_dir)
    if not filepath.exists():
        return []
    
    events = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                event = SwarmEvent(
                    id=data.get("id", ""),
                    type=data.get("type", ""),
                    swarm_id=data.get("swarm_id", ""),
                    agent_id=data.get("agent_id", ""),
                    session_id=data.get("session_id"),
                    timestamp=data.get("timestamp", ""),
                    data=data.get("data", {}),
                )
                
                # Filter
                if swarm_id and event.swarm_id != swarm_id:
                    continue
                if agent_id and event.agent_id != agent_id:
                    continue
                if event_type and event.type != event_type:
                    continue
                
                events.append(event)
            except json.JSONDecodeError:
                continue
    
    # Neueste zuerst
    events.reverse()
    return events[:limit]


def get_event_counts(
    swarm_id: Optional[str] = None,
    base_dir: str | Path = ".",
) -> dict[str, int]:
    """Zähle Events nach Typ"""
    events = load_events(swarm_id=swarm_id, limit=10000, base_dir=base_dir)
    counts: dict[str, int] = {}
    for event in events:
        counts[event.type] = counts.get(event.type, 0) + 1
    return counts


def recent_events(
    limit: int = 10,
    swarm_id: Optional[str] = None,
    base_dir: str | Path = ".",
) -> list[SwarmEvent]:
    """Hole die neuesten Events"""
    return load_events(swarm_id=swarm_id, limit=limit, base_dir=base_dir)
