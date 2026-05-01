"""
Agent Registry — Registry-driven Subagent Resolution
Portiert aus Plugin-SIN-Swarm lib/swarm-registry.ts (SOTA)
Ersetzt title-derived Routing mit durablem Member Registry

KEIN tmux, KEINE Worktrees — reine Config-basierte Auflösung
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime


# --- Legacy Aliases (für Rückwärtskompatibilität) ---
LEGACY_ALIASES: dict[str, string] = {
    "planner": "plan",
    "researcher": "explore",
    "coder": "build",
    "reviewer": "general",
}

CANONICAL_AGENTS = ["plan", "explore", "build", "general"]


@dataclass
class RegistryEntry:
    """Ein Eintrag im Agenten-Registry"""
    member_name: str
    agent_id: str
    schema_version: int = 2
    capabilities: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_seen_at: Optional[str] = None


@dataclass
class SwarmRegistry:
    """Vollständiges Agenten-Registry"""
    version: int = 2
    swarm_id: str = "code-swarm"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    members: dict[str, RegistryEntry] = field(default_factory=dict)


def resolve_agent_id(member_name: str, explicit_agent: Optional[str] = None) -> str:
    """
    Löse Agent-ID auf, mit Legacy-Alias-Unterstützung.
    
    Args:
        member_name: Name des Members (z.B. "planner", "athena")
        explicit_agent: Explizite Agent-ID (überschreibt Alias)
    
    Returns:
        Aufgelöste Agent-ID (z.B. "plan", "explore")
    """
    if explicit_agent and explicit_agent.strip():
        return explicit_agent.strip()
    
    normalized = member_name.strip().lower()
    return LEGACY_ALIASES.get(normalized, member_name)


def get_unknown_agent_diagnostic(agent_id: str, member_name: str) -> str:
    """Erstelle Diagnose-Message für unbekannte Agenten"""
    valid_aliases = ", ".join(LEGACY_ALIASES.keys())
    canonical_names = ", ".join(CANONICAL_AGENTS)
    
    return (
        f"Unbekannte Agent-ID '{agent_id}' für Member '{member_name}'.\n"
        f"Gültige Aliase: {valid_aliases}\n"
        f"Kanomische Agenten: {canonical_names}"
    )


class AgentRegistry:
    """Registry-driven Subagent Resolution — primäre Quelle der Wahrheit"""

    def __init__(self, registry_dir: str | Path = ".code-swarm/registry"):
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, SwarmRegistry] = {}

    def _registry_path(self, swarm_id: str) -> Path:
        return self.registry_dir / f"{swarm_id}.json"

    def save(self, registry: SwarmRegistry) -> None:
        """Speichere Registry auf Disk"""
        path = self._registry_path(registry.swarm_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": registry.version,
            "swarm_id": registry.swarm_id,
            "created_at": registry.created_at,
            "members": {
                name: asdict(entry)
                for name, entry in registry.members.items()
            },
        }
        path.write_text(json.dumps(data, indent=2))
        self._cache[registry.swarm_id] = registry

    def load(self, swarm_id: str = "code-swarm") -> Optional[SwarmRegistry]:
        """Lade Registry von Disk"""
        if swarm_id in self._cache:
            return self._cache[swarm_id]
        
        path = self._registry_path(swarm_id)
        if not path.exists():
            return None
        
        try:
            data = json.loads(path.read_text())
            members = {}
            for name, entry_data in data.get("members", {}).items():
                members[name] = RegistryEntry(
                    member_name=entry_data["member_name"],
                    agent_id=entry_data["agent_id"],
                    schema_version=entry_data.get("schema_version", 1),
                    capabilities=entry_data.get("capabilities", []),
                    created_at=entry_data.get("created_at", ""),
                    last_seen_at=entry_data.get("last_seen_at"),
                )
            
            registry = SwarmRegistry(
                version=data.get("version", 1),
                swarm_id=data.get("swarm_id", swarm_id),
                created_at=data.get("created_at", ""),
                members=members,
            )
            self._cache[swarm_id] = registry
            return registry
        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️ Registry {swarm_id} korrupt: {e}")
            return None

    def register_member(
        self,
        member_name: str,
        agent_id: str,
        capabilities: list[str] | None = None,
        swarm_id: str = "code-swarm",
    ) -> RegistryEntry:
        """Registriere einen neuen Member"""
        registry = self.load(swarm_id) or SwarmRegistry(swarm_id=swarm_id)
        
        entry = RegistryEntry(
            member_name=member_name.strip().lower(),
            agent_id=resolve_agent_id(member_name, agent_id),
            capabilities=capabilities or [],
            last_seen_at=datetime.utcnow().isoformat(),
        )
        registry.members[entry.member_name] = entry
        self.save(registry)
        return entry

    def resolve_member(
        self,
        member_name: str,
        swarm_id: str = "code-swarm",
    ) -> Optional[RegistryEntry]:
        """Löse Member über Registry auf (Primary) + Alias (Fallback)"""
        registry = self.load(swarm_id)
        normalized = member_name.strip().lower()
        
        # 1. Registry (Primary)
        if registry and normalized in registry.members:
            return registry.members[normalized]
        
        # 2. Alias (Fallback)
        resolved = resolve_agent_id(member_name)
        if resolved != normalized:
            return RegistryEntry(
                member_name=normalized,
                agent_id=resolved,
            )
        
        return None

    def list_members(self, swarm_id: str = "code-swarm") -> list[RegistryEntry]:
        """Liste alle registrierten Members"""
        registry = self.load(swarm_id)
        if not registry:
            return []
        return list(registry.members.values())
