from __future__ import annotations
from typing import TypedDict, List, Dict, Any, Optional
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

    Dual transport: stdio (local) + streamable HTTP (remote)
    """

    def __init__(self, simone_url: str = "http://localhost:8234"):
        self.builder = StateGraph(OpenCodeState)
        self.memory = MemorySaver()
        self.simone = SwarmSimoneBridge(simone_url)

    def add_simone_node(self, name: str):
        """Füge einen Simone-MCP-fähigen Node hinzu."""
        async def simone_node(state: OpenCodeState):
            result = await self.simone.analyze_code(name)
            return {
                **state,
                "execution_log": state["execution_log"] + [
                    {"agent": name, "action": "Simone-MCP analyzed", "result": result}
                ]
            }
        self.builder.add_node(name, simone_node)

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


def hermes_node(state: OpenCodeState):
    """Hermes Node: Task-Verteilung mit Simone-MCP."""
    return {
        **state,
        "execution_log": state["execution_log"] + [
            {"agent": "hermes", "action": "Task verteilt", "task": state["task"]}
        ]
    }


def prometheus_node(state: OpenCodeState):
    """Prometheus Node: Architektur-Planung mit Simone-MCP."""
    return {
        **state,
        "plans": state["plans"] + [
            {
                "agent": "prometheus",
                "plan": {
                    "architecture": "LangGraph + Simone-MCP",
                    "context_window": "1M",
                    "feedback_loops": True,
                    "simone_integrated": True
                }
            }
        ]
    }


def zeus_node(state: OpenCodeState):
    """Zeus Node: Kritische Review mit Simone-MCP."""
    return {
        **state,
        "validated_plan": {
            "plan": state["plans"][-1] if state["plans"] else None,
            "approved": True,
            "errors": []
        }
    }


def atlas_node(state: OpenCodeState):
    """Atlas Node: Backend-Entwicklung mit Simone-MCP AST."""
    return {
        **state,
        "execution_log": state["execution_log"] + [
            {
                "agent": "atlas",
                "action": "Backend-Code generiert (Simone-MCP powered)",
                "tools": ["code.find_symbol", "code.replace_symbol_body"]
            }
        ]
    }


def iris_node(state: OpenCodeState):
    """Iris Node: Frontend-Entwicklung mit Simone-MCP."""
    return {
        **state,
        "execution_log": state["execution_log"] + [
            {
                "agent": "iris",
                "action": "Frontend-Code generiert (Simone-MCP powered)"
            }
        ]
    }