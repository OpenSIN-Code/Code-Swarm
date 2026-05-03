"""Neo4j graph memory adapter."""
from __future__ import annotations
from typing import Any


class Neo4jAdapter:
    def __init__(self, uri: str = "bolt://localhost:7687"):
        self.uri = uri
        self._nodes: list[dict[str, Any]] = []
        self._edges: list[dict[str, Any]] = []

    def create_entity(self, entity_type: str, properties: dict[str, Any]) -> str:
        node_id = f"{entity_type}_{len(self._nodes)}"
        self._nodes.append({"id": node_id, "type": entity_type, "properties": properties})
        return node_id

    def create_relation(self, from_id: str, to_id: str, rel_type: str) -> None:
        self._edges.append({"from": from_id, "to": to_id, "type": rel_type})

    def get_related(self, node_id: str, rel_type: str | None = None) -> list[dict[str, Any]]:
        results = []
        for edge in self._edges:
            if edge["from"] == node_id:
                if rel_type is None or edge["type"] == rel_type:
                    target = next((n for n in self._nodes if n["id"] == edge["to"]), None)
                    if target:
                        results.append(target)
        return results

    def health(self) -> dict[str, Any]:
        return {"status": "ok", "nodes": len(self._nodes), "edges": len(self._edges)}
