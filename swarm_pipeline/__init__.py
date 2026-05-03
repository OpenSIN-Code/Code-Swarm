"""Code-Swarm pipeline orchestration package.

Built on top of the PyPI ``langgraph`` package; this local namespace was
renamed from ``langgraph`` to avoid shadowing the third-party module.
"""
from .graph import LangGraphPipeline, create_default_pipeline
from .recursive_link import RecursiveMASBridge, Adapter, CrossModelAdapter
from .state import OpenCodeState

__all__ = [
    "LangGraphPipeline",
    "OpenCodeState",
    "RecursiveMASBridge",
    "Adapter",
    "CrossModelAdapter",
    "create_default_pipeline",
]
