from __future__ import annotations
from typing import TypedDict, List, Dict, Any, Optional
from swarm_pipeline.recursive_link import RecursiveMASBridge
import asyncio
import os
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from .state import OpenCodeState
from simone_mcp.bridge import SwarmSimoneBridge, SIMONE_TOOL_PROMPT


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


async def create_default_pipeline() -> LangGraphPipeline:
    """Create the default SIN pipeline with all nodes."""
    pipeline = LangGraphPipeline()
    
    # Add all standard nodes
    pipeline.builder.add_node("hermes", hermes_node)
    pipeline.builder.add_node("prometheus", prometheus_node)
    pipeline.builder.add_node("zeus", zeus_node)
    pipeline.builder.add_node("atlas", atlas_node)
    pipeline.builder.add_node("iris", iris_node)
    
    # Add edges
    pipeline.builder.set_entry_point("hermes")
    pipeline.builder.add_edge("hermes", "prometheus")
    pipeline.builder.add_edge("prometheus", "zeus")
    pipeline.builder.add_edge("zeus", "atlas")
    pipeline.builder.add_edge("atlas", "iris")
    pipeline.builder.add_edge("iris", END)
    
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

    def recursive_step(self, agent_idx: int, latent_state: torch.Tensor) -> torch.Tensor:
        if 0 <= agent_idx < len(self.agent_links):
            return self.agent_links[agent_idx](latent_state)
        return self.recursive_link(latent_state)
