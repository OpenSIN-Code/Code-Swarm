"""Hybrid retrieval combining vector + graph memory."""
from __future__ import annotations
from typing import Any

from memory.qdrant_adapter import QdrantAdapter
from memory.neo4j_adapter import Neo4jAdapter


class HybridRetriever:
    def __init__(self, vector_adapter: QdrantAdapter, graph_adapter: Neo4jAdapter):
        self.vector = vector_adapter
        self.graph = graph_adapter

    def retrieve(self, query_vector: list[float], context_id: str | None = None, limit: int = 5) -> list[dict[str, Any]]:
        vector_results = self.vector.search("agent_memories", query_vector, limit)
        if context_id:
            graph_results = self.graph.get_related(context_id)
            for g in graph_results:
                g["source"] = "graph"
                if g not in vector_results:
                    vector_results.append(g)
        return vector_results[:limit]

    def health(self) -> dict[str, Any]:
        return {
            "vector": self.vector.health(),
            "graph": self.graph.health(),
        }
