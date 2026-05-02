from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
import numpy as np
import hashlib


class VectorDB:
    """Local vector database with cosine similarity search (pgvector simulation)"""

    def __init__(self, base_dir: str | Path = ".", dimension: int = 1536):
        self.base_dir = Path(base_dir)
        self.dimension = dimension
        self._vector_dir = self.base_dir / ".code-swarm" / "vector"
        self._vector_dir.mkdir(parents=True, exist_ok=True)
        self._vectors_file = self._vector_dir / "vectors.json"
        self._vectors: dict[str, dict] = {}
        self._load()

    def _load(self):
        if self._vectors_file.exists():
            self._vectors = json.loads(self._vectors_file.read_text())

    def _save(self):
        self._vectors_file.write_text(json.dumps(self._vectors))

    def _normalize(self, vector: list[float]) -> list[float]:
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return [v / norm for v in vector]

    def insert(self, key: str, vector: list[float], metadata: Optional[dict] = None):
        normalized = self._normalize(vector)
        self._vectors[key] = {
            "vector": normalized,
            "metadata": metadata or {},
        }
        self._save()

    def search(self, query_vector: list[float], top_k: int = 5) -> list[dict]:
        if not self._vectors:
            return []
        
        normalized_query = self._normalize(query_vector)
        results = []
        
        for key, data in self._vectors.items():
            vec = np.array(data["vector"])
            query = np.array(normalized_query)
            similarity = float(np.dot(vec, query))
            results.append({
                "key": key,
                "similarity": similarity,
                "metadata": data["metadata"],
            })
        
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def delete(self, key: str):
        if key in self._vectors:
            del self._vectors[key]
            self._save()

    def count(self) -> int:
        return len(self._vectors)