# 🔥 Code-Swarm: Agenten-Swarm Kernbibliothek
# Fusioniert SOTA Patterns aus Plugin-SIN-Swarm + omoc-swarm
# KEIN tmux, KEINE Worktrees, KEIN Background-Dispatch
# opencode-native Subagent-Delegation

from .registry import AgentRegistry, resolve_agent_id, LEGACY_ALIASES
from .events import SwarmEvent, append_event, load_events, recent_events
from .memory import remember, load_memory, MemoryEntry
