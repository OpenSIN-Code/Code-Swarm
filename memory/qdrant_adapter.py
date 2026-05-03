"""Qdrant vector memory adapter."""
from __future__ import annotations
import json
from typing import Any


class QdrantAdapter:
    def __init__(self, url: str = "http://localhost:6333"):
        self.url = url
        self._vectors: list[dict[str, Any]] = []

    def upsert(self, collection: str, vector: list[float], payload: dict[str, Any]) -> None:
        self._vectors.append({"collection": collection, "vector": vector, "payload": payload})

    def search(self, collection: str, vector: list[float], limit: int = 5) -> list[dict[str, Any]]:
        results = []
        for v in self._vectors:
            if v["collection"] == collection:
                sim = sum(a * b for a, b in zip(v["vector"], vector))
                results.append({"score": sim, "payload": v["payload"]})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def health(self) -> dict[str, Any]:
        return {"status": "ok", "vectors": len(self._vectors)}
