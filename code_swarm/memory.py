"""
Swarm Memory — Persistentes Lernen aus Agenten-Erfahrungen
Portiert aus Plugin-SIN-Swarm plugins/state.ts (SOTA)
Ermöglicht Cross-Session-Learning und Feedback-Loops

KEIN tmux, KEINE Worktrees — reine JSON-basierte Persistenz
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid


@dataclass
class MemoryEntry:
    """Ein Memory-Eintrag"""
    id: str = field(default_factory=lambda: f"mem_{uuid.uuid4().hex[:12]}")
    swarm_id: str = "code-swarm"
    agent_id: str = ""
    key: str = ""
    value: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def _memory_dir(base_dir: str | Path = ".") -> Path:
    path = Path(base_dir) / ".code-swarm" / "memory"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _memory_file(base_dir: str | Path = ".") -> Path:
    return _memory_dir(base_dir) / "memory.json"


def remember(
    agent_id: str,
    key: str,
    value: str,
    tags: list[str] | None = None,
    swarm_id: str = "code-swarm",
    base_dir: str | Path = ".",
) -> MemoryEntry:
    """
    Speichere eine Lernerfahrung (Upsert).
    
    Args:
        agent_id: ID des Agenten
        key: Eindeutiger Schlüssel (z.B. "prompt.atlas.v2", "feedback.hermes")
        value: Wert (z.B. der optimierte Prompt, das Feedback)
        tags: Kategorien für spätere Suche
        swarm_id: Swarm-ID
        base_dir: Basis-Verzeichnis
    
    Returns:
        Der erstellte/aktualisierte MemoryEntry
    
    Example:
        >>> remember("atlas", "prompt.effective", "Use more specific types",
        ...          tags=["prompt", "optimization"])
    """
    entries = _load_all(base_dir)
    existing = None
    for entry in entries:
        if entry.swarm_id == swarm_id and entry.agent_id == agent_id and entry.key == key:
            existing = entry
            break
    
    now = datetime.now(timezone.utc).isoformat()
    
    if existing:
        existing.value = value
        if tags:
            existing.tags = list(set(list(existing.tags) + tags))
        existing.updated_at = now
        entry = existing
    else:
        entry = MemoryEntry(
            swarm_id=swarm_id,
            agent_id=agent_id,
            key=key,
            value=value,
            tags=tags or [],
        )
        entries.append(entry)
    
    _save_all(entries, base_dir)
    return entry


def load_memory(
    agent_id: Optional[str] = None,
    key: Optional[str] = None,
    tags: Optional[list[str]] = None,
    swarm_id: str = "code-swarm",
    base_dir: str | Path = ".",
) -> list[MemoryEntry]:
    """
    Lade Memory-Einträge mit optionalen Filtern.
    
    Args:
        agent_id: Filter nach Agent
        key: Filter nach Schlüssel
        tags: Filter nach Tags (muss ALLE enthalten)
        swarm_id: Swarm-ID
        base_dir: Basis-Verzeichnis
    
    Returns:
        Gefilterte Memory-Einträge
    """
    entries = _load_all(base_dir)
    result = []
    
    for entry in entries:
        if entry.swarm_id != swarm_id:
            continue
        if agent_id and entry.agent_id != agent_id:
            continue
        if key and entry.key != key:
            continue
        if tags:
            if not all(tag in entry.tags for tag in tags):
                continue
        
        result.append(entry)
    
    return result


def _load_all(base_dir: str | Path = ".") -> list[MemoryEntry]:
    filepath = _memory_file(base_dir)
    if not filepath.exists():
        return []
    
    try:
        data = json.loads(filepath.read_text())
        return [MemoryEntry(**entry) for entry in data]
    except (json.JSONDecodeError, TypeError):
        return []


def _save_all(entries: list[MemoryEntry], base_dir: str | Path = ".") -> None:
    filepath = _memory_file(base_dir)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    data = []
    for entry in entries:
        data.append({
            "id": entry.id,
            "swarm_id": entry.swarm_id,
            "agent_id": entry.agent_id,
            "key": entry.key,
            "value": entry.value,
            "tags": entry.tags,
            "created_at": entry.created_at,
            "updated_at": entry.updated_at,
        })
    
    filepath.write_text(json.dumps(data, indent=2))
