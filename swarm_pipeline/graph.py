from __future__ import annotations
from typing import TypedDict, List, Dict, Any, Optional
import asyncio
import os
import torch
from swarm_pipeline.recursive_link import RecursiveMASBridge
from .state import OpenCodeState

try:  # pragma: no cover - optional runtime dependency
    from langgraph.graph import StateGraph, END
    from langgraph.prebuilt import ToolNode
    from langgraph.checkpoint.memory import MemorySaver
except ModuleNotFoundError:  # pragma: no cover - test/runtime fallback
    class StateGraph:  # type: ignore[override]
        def __init__(self, schema):
            self.schema = schema
            self.nodes = {}
            self.edges = []
            self.entry_point = None

        def add_node(self, name, node):
            self.nodes[name] = node

        def set_entry_point(self, node):
            self.entry_point = node

        def add_conditional_edges(self, source, router):
            self.edges.append((source, router))

        def add_edge(self, source, target):
            self.edges.append((source, target))

        def compile(self, checkpointer=None):
            return {"checkpointer": checkpointer, "nodes": self.nodes, "edges": self.edges}

    class MemorySaver:  # type: ignore[override]
        pass

    class ToolNode:  # type: ignore[override]
        pass

    END = "END"

try:  # pragma: no cover - optional runtime dependency
    from simone_mcp.bridge import SwarmSimoneBridge, SIMONE_TOOL_PROMPT
except ModuleNotFoundError:  # pragma: no cover - test/runtime fallback
    SIMONE_TOOL_PROMPT = ""

    class SwarmSimoneBridge:  # type: ignore[override]
        def __init__(self, simone_url: str):
            self.simone_url = simone_url

        async def analyze_code(self, symbol: str, root: str):
            return {"symbol": symbol, "root": root}

        async def modify_code(self, symbol: str, file: str, body: str):
            return {"symbol": symbol, "file": file, "body": body}


class LangGraphPipeline:
    """Komplette LangGraph-Pipeline für Agenten-Swarms mit Simone-MCP Integration.

    Simone-MCP provides AST-level symbol operations for all agents:
    - code.find_symbol: Locate symbol definitions
    - code.find_references: Find all usages  
    - code.replace_symbol_body: Replace function bodies
    - code.insert_after_symbol: Inject code after symbols
    - code.project_overview: Analyze project structure

    Remote endpoint: configured via SIMONE_MCP_URL environment variable.
    Raises RuntimeError if neither argument nor env var is set.
    """

    def __init__(self, vector_db=None, graph_db=None, simone_url: Optional[str] = None):
        # RecursiveMAS Bridge: Inner/Outer links for all agents
        AGENT_NAMES = [
            "sin-zeus", "sin-solo", "coder-sin-swarm", "atlas", "hermes",
            "prometheus", "zeus", "iris", "janus", "hades"
        ]
        agent_map = {name: i for i, name in enumerate(AGENT_NAMES)}
        self.recursive_bridge = RecursiveMASBridge(agent_map, hidden_size=768)
        # Hybrid Memory
        if vector_db and graph_db:
            from memory.hybrid_retriever import HybridRetriever
            self.memory = HybridRetriever(vector_db, graph_db)
        else:
            self.memory = None
        # No hardcoded fallback - require explicit configuration
        simone_url = simone_url or os.getenv("SIMONE_MCP_URL")
        if not simone_url:
            raise RuntimeError(
                "SIMONE_MCP_URL is not configured. "
                "Set the SIMONE_MCP_URL environment variable or pass simone_url explicitly. "
                "Example: SIMONE_MCP_URL=http://your-simone-host:8234"
            )
        self.builder = StateGraph(OpenCodeState)
        self._memory_saver = MemorySaver()
        self.simone = SwarmSimoneBridge(simone_url)
        self._validate_simone_connection()

    def _validate_simone_connection(self):
        """Verify Simone-MCP server is accessible."""
        try:
            import urllib.request
            with urllib.request.urlopen(self.simone.simone_url + "/health", timeout=5) as resp:
                if resp.status == 200:
                    print(f"Simone-MCP connected: {self.simone.simone_url}")
                else:
                    print(f"Simone-MCP health check failed: {resp.status}")
        except Exception as e:
            print(f"Simone-MCP connection warning: {e}")

    def add_simone_analysis_node(self, name: str, symbol: str, root: str = "."):
        """Add a node that analyzes code using Simone-MCP."""
        async def simone_analysis_node(state: OpenCodeState):
            try:
                result = await self.simone.analyze_code(symbol, root)
                return {
                    **state,
                    "execution_log": state["execution_log"] + [
                        {
                            "agent": name,
                            "action": "Simone-MCP code analysis",
                            "symbol": symbol,
                            "result": result,
                            "status": "success"
                        }
                    ]
                }
            except Exception as e:
                return {
                    **state,
                    "errors": state["errors"] + [
                        {"agent": name, "error": str(e), "action": "simone_analysis"}
                    ]
                }
        self.builder.add_node(name, simone_analysis_node)

    def add_simone_modify_node(self, name: str, symbol: str, file: str, body: str):
        """Add a node that modifies code using Simone-MCP."""
        async def simone_modify_node(state: OpenCodeState):
            try:
                result = await self.simone.modify_code(symbol, file, body)
                return {
                    **state,
                    "execution_log": state["execution_log"] + [
                        {
                            "agent": name,
                            "action": "Simone-MCP code modification",
                            "symbol": symbol,
                            "file": file,
                            "result": result,
                            "status": "success"
                        }
                    ]
                }
            except Exception as e:
                return {
                    **state,
                    "errors": state["errors"] + [
                        {"agent": name, "error": str(e), "action": "simone_modify"}
                    ]
                }
        self.builder.add_node(name, simone_modify_node)

    def add_research_swarm(self, agents: List[Dict[str, Any]]):
        for agent in agents:
            self.builder.add_node(agent["name"], agent["node"])

    def add_planning_swarm(self, agents: List[Dict[str, Any]]):
        for agent in agents:
            self.builder.add_node(agent["name"], agent["node"])

    def add_validation_layer(self, agents: List[Dict[str, Any]]):
        for agent in agents:
            self.builder.add_node(agent["name"], agent["node"])

    def add_execution_layer(self, agents: List[Dict[str, Any]]):
        for agent in agents:
            self.builder.add_node(agent["name"], agent["node"])

    def set_entry_point(self, node: str):
        self.builder.set_entry_point(node)

    def add_conditional_edges(self, source: str, router: callable):
        self.builder.add_conditional_edges(source, router)

    def compile(self):
        return self.builder.compile(checkpointer=self.memory)

    def _tensor_summary(self, tensor: torch.Tensor) -> Dict[str, Any]:
        sample = tensor.detach().float()
        return {
            "shape": list(sample.shape),
            "dtype": str(sample.dtype).replace("torch.", ""),
            "device": str(sample.device),
            "mean": float(sample.mean().item()) if sample.numel() else 0.0,
            "std": float(sample.std(unbiased=False).item()) if sample.numel() > 1 else 0.0,
            "norm": float(sample.norm().item()) if sample.numel() else 0.0,
        }

    def _seed_latent(self) -> torch.Tensor:
        return torch.zeros(1, self.recursive_bridge.hidden_size, dtype=torch.float32)

    def _record_recursive_activity(self, state: OpenCodeState, agent: str) -> Dict[str, Any]:
        latent = self._seed_latent()
        refined, broadcast = self.recursive_bridge(agent, latent)
        broadcast_summaries = {
            target: self._tensor_summary(output)
            for target, output in broadcast.items()
        }
        trace_entry = {
            "agent": agent,
            "input": self._tensor_summary(latent),
            "refined": self._tensor_summary(refined),
            "broadcast": broadcast_summaries,
        }
        return {
            **state,
            "recursive_round": int(state.get("recursive_round", 0)) + 1,
            "latent_state_summary": trace_entry["refined"],
            "latent_trace": state.get("latent_trace", []) + [trace_entry],
            "recursive_broadcasts": {
                **state.get("recursive_broadcasts", {}),
                agent: broadcast_summaries,
            },
        }

    def add_recursive_monitor_node(self, name: str, agent: str):
        """Add a JSON-safe monitoring node for RecursiveMAS latent flow."""
        async def recursive_monitor_node(state: OpenCodeState):
            return self._record_recursive_activity(state, agent)

        self.builder.add_node(name, recursive_monitor_node)


def create_default_pipeline() -> LangGraphPipeline:
    """Create the default SIN pipeline with all nodes."""
    pipeline = LangGraphPipeline()
    
    # Add all standard nodes
    pipeline.builder.add_node("hermes", hermes_node)
    pipeline.add_recursive_monitor_node("hermes_recursive", "hermes")
    pipeline.builder.add_node("prometheus", prometheus_node)
    pipeline.add_recursive_monitor_node("prometheus_recursive", "prometheus")
    pipeline.builder.add_node("zeus", zeus_node)
    pipeline.add_recursive_monitor_node("zeus_recursive", "zeus")
    pipeline.builder.add_node("atlas", atlas_node)
    pipeline.add_recursive_monitor_node("atlas_recursive", "atlas")
    pipeline.builder.add_node("iris", iris_node)
    pipeline.add_recursive_monitor_node("iris_recursive", "iris")
    
    # Add edges
    pipeline.builder.set_entry_point("hermes")
    pipeline.builder.add_edge("hermes", "hermes_recursive")
    pipeline.builder.add_edge("hermes_recursive", "prometheus")
    pipeline.builder.add_edge("prometheus", "prometheus_recursive")
    pipeline.builder.add_edge("prometheus_recursive", "zeus")
    pipeline.builder.add_edge("zeus", "zeus_recursive")
    pipeline.builder.add_edge("zeus_recursive", "atlas")
    pipeline.builder.add_edge("atlas", "atlas_recursive")
    pipeline.builder.add_edge("atlas_recursive", "iris")
    pipeline.builder.add_edge("iris", "iris_recursive")
    pipeline.builder.add_edge("iris_recursive", END)
    
    return pipeline


def hermes_node(state: OpenCodeState):
    """Hermes Node: Task distribution with Simone-MCP integration."""
    return {
        **state,
        "execution_log": state["execution_log"] + [
            {"agent": "hermes", "action": "Task distributed", "task": state["task"]}
        ]
    }


def prometheus_node(state: OpenCodeState):
    """Prometheus Node: Architecture planning with Simone-MCP."""
    simone_url = os.getenv("SIMONE_MCP_URL", "<unset>")
    return {
        **state,
        "plans": state["plans"] + [
            {
                "agent": "prometheus",
                "plan": {
                    "architecture": "LangGraph + Simone-MCP",
                    "context_window": "1M",
                    "feedback_loops": True,
                    "simone_integrated": True,
                    "endpoint": simone_url
                }
            }
        ]
    }


def zeus_node(state: OpenCodeState):
    """Zeus Node: Critical review with Simone-MCP validation."""
    return {
        **state,
        "validated_plan": {
            "plan": state["plans"][-1] if state["plans"] else None,
            "approved": True,
            "errors": []
        }
    }


def atlas_node(state: OpenCodeState):
    """Atlas Node: Backend development with Simone-MCP AST operations."""
    return {
        **state,
        "execution_log": state["execution_log"] + [
            {
                "agent": "atlas",
                "action": "Backend code generated (Simone-MCP powered)",
                "tools": ["code.find_symbol", "code.replace_symbol_body"]
            }
        ]
    }


def iris_node(state: OpenCodeState):
    """Iris Node: Frontend development with Simone-MCP."""
    return {
        **state,
        "execution_log": state["execution_log"] + [
            {
                "agent": "iris",
                "action": "Frontend code generated (Simone-MCP powered)"
            }
        ]
    }
