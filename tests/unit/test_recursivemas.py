from __future__ import annotations

import sys
import types
from pathlib import Path

import torch
from typer.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def _install_optional_dependency_stubs() -> None:
    if "langgraph" not in sys.modules:
        langgraph = types.ModuleType("langgraph")
        langgraph.__path__ = []  # type: ignore[attr-defined]

        graph_mod = types.ModuleType("langgraph.graph")
        prebuilt_mod = types.ModuleType("langgraph.prebuilt")
        checkpoint_mod = types.ModuleType("langgraph.checkpoint")
        checkpoint_mod.__path__ = []  # type: ignore[attr-defined]
        memory_mod = types.ModuleType("langgraph.checkpoint.memory")

        class _DummyStateGraph:
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

        class _DummyMemorySaver:
            pass

        graph_mod.StateGraph = _DummyStateGraph
        graph_mod.END = "END"
        prebuilt_mod.ToolNode = object
        memory_mod.MemorySaver = _DummyMemorySaver

        checkpoint_mod.memory = memory_mod
        langgraph.graph = graph_mod
        langgraph.prebuilt = prebuilt_mod
        langgraph.checkpoint = checkpoint_mod

        sys.modules.update(
            {
                "langgraph": langgraph,
                "langgraph.graph": graph_mod,
                "langgraph.prebuilt": prebuilt_mod,
                "langgraph.checkpoint": checkpoint_mod,
                "langgraph.checkpoint.memory": memory_mod,
            }
        )

    if "simone_mcp" not in sys.modules:
        simone_mcp = types.ModuleType("simone_mcp")
        simone_mcp.__path__ = []  # type: ignore[attr-defined]
        bridge_mod = types.ModuleType("simone_mcp.bridge")

        class _DummySimoneBridge:
            def __init__(self, simone_url: str):
                self.simone_url = simone_url

            async def analyze_code(self, symbol: str, root: str):
                return {"symbol": symbol, "root": root}

            async def modify_code(self, symbol: str, file: str, body: str):
                return {"symbol": symbol, "file": file, "body": body}

        bridge_mod.SwarmSimoneBridge = _DummySimoneBridge
        bridge_mod.SIMONE_TOOL_PROMPT = "stub"
        simone_mcp.bridge = bridge_mod

        sys.modules.update(
            {
                "simone_mcp": simone_mcp,
                "simone_mcp.bridge": bridge_mod,
            }
        )


_install_optional_dependency_stubs()

from cli.main import app
from cli.recursivemas import build_run_command, format_style_summary, missing_runtime_dependencies
from recursivemas.load_from_repo import SUPPORTED_BENCHMARKS, describe_style, list_supported_styles
from swarm_pipeline.graph import LangGraphPipeline, create_default_pipeline
from swarm_pipeline.recursive_link import RecursiveMASBridge


def test_recursivemas_styles_metadata_is_complete():
    styles = list_supported_styles()

    assert set(styles) == {
        "sequential_light",
        "sequential_scaled",
        "mixture",
        "distillation",
        "deliberation",
    }

    summary = describe_style("sequential_light")
    assert summary["display_name"] == "Sequential (Light)"
    assert summary["recommended_batch_size"] == 32
    assert len(SUPPORTED_BENCHMARKS) == 9


def test_recursivemas_command_builder_uses_style_defaults():
    command = build_run_command("mixture", dataset="math500", device="cuda")

    assert command[0] == sys.executable
    assert command[1].endswith("recursivemas/run.py")
    assert "--style" in command and "mixture" in command
    assert "--batch_size" in command and "16" in command
    assert "--device" in command and "cuda" in command


def test_runtime_dependency_check_reports_state():
    missing = missing_runtime_dependencies()

    assert isinstance(missing, list)


def test_recursivemas_style_summary_mentions_roles():
    summary = format_style_summary("deliberation")

    assert "Reflector" in summary
    assert "Tool-Caller" in summary or "toolcaller" in summary
    assert "Qwen3.5-4B" in summary


def test_recursivemas_bridge_forward_and_topology():
    bridge = RecursiveMASBridge(
        {"planner": 0, "critic": 1},
        hidden_size=4,
        topology={"planner": ["critic"], "critic": ["planner"]},
    )

    latent = torch.randn(1, 4)
    refined, outputs = bridge("planner", latent)

    assert refined.shape == latent.shape
    assert set(outputs) == {"critic"}
    assert outputs["critic"].shape == latent.shape
    assert len(list(bridge.parameters())) > 0


def test_langgraph_pipeline_records_recursive_activity(monkeypatch):
    class DummySimoneBridge:
        def __init__(self, simone_url: str):
            self.simone_url = simone_url

        async def analyze_code(self, symbol: str, root: str):
            return {"symbol": symbol, "root": root}

        async def modify_code(self, symbol: str, file: str, body: str):
            return {"symbol": symbol, "file": file, "body": body}

    monkeypatch.setattr("swarm_pipeline.graph.SwarmSimoneBridge", DummySimoneBridge)
    monkeypatch.setattr(LangGraphPipeline, "_validate_simone_connection", lambda self: None)

    pipeline = LangGraphPipeline(simone_url="http://example.invalid")
    state = {
        "task": "demo",
        "research": [],
        "plans": [],
        "validated_plan": {},
        "execution_log": [],
        "memory": {},
        "errors": [],
        "feedback": [],
        "metrics": {},
        "recursive_round": 0,
        "latent_trace": [],
        "latent_state_summary": {},
        "recursive_broadcasts": {},
    }

    updated = pipeline._record_recursive_activity(state, "hermes")

    assert updated["recursive_round"] == 1
    assert len(updated["latent_trace"]) == 1
    assert updated["latent_trace"][0]["agent"] == "hermes"
    assert updated["latent_state_summary"]["shape"] == [1, 768]


def test_default_pipeline_includes_recursive_nodes(monkeypatch):
    monkeypatch.setenv("SIMONE_MCP_URL", "http://example.invalid")
    monkeypatch.setattr(LangGraphPipeline, "_validate_simone_connection", lambda self: None)

    pipeline = create_default_pipeline()

    assert "hermes_recursive" in pipeline.builder.nodes
    assert "prometheus_recursive" in pipeline.builder.nodes
    assert pipeline.builder.entry_point == "hermes"


def test_cli_recursivemas_styles_command():
    runner = CliRunner()
    result = runner.invoke(app, ["mas", "styles"])

    assert result.exit_code == 0
    assert "RecursiveMAS Styles" in result.output
    assert "sequential_light" in result.output


def test_cli_recursivemas_benchmark_dry_run():
    runner = CliRunner()
    result = runner.invoke(app, ["mas", "benchmark", "mixture", "--dry-run", "--device", "cpu"])

    assert result.exit_code == 0
    assert "recursivemas/run.py" in result.output
    assert "--style mixture" in result.output or "mixture" in result.output
