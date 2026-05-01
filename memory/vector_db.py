import faiss
import numpy as np
from typing import List, Dict, Any

class VectorDB:
    """Vektordatenbank für Memory Layer."""
    
    def __init__(self, dimension: int = 512):
        self.index = faiss.IndexFlatL2(dimension)
        self.memory = {}  # Speichert Kontext
        self.dimension = dimension
    
    def add(self, vector: List[float], key: str, metadata: Dict[str, Any] = None):
        """Füge einen Vektor zur Datenbank hinzu."""
        vector_array = np.array([vector], dtype=np.float32)
        self.index.add(vector_array)
        self.memory[key] = {
            "vector": vector,
            "metadata": metadata or {}
        }
    
    def search(self, query_vector: List[float], k: int = 4) -> List[Dict[str, Any]]:
        """Suche ähnliche Vektoren."""
        query_array = np.array([query_vector], dtype=np.float32)
        distances, indices = self.index.search(query_array, k)
        return [
            {
                "key": list(self.memory.keys())[i],
                "vector": self.memory[list(self.memory.keys())[i]]["vector"],
                "metadata": self.memory[list(self.memory.keys())[i]]["metadata"],
                "distance": distances[0][i]
            }
            for i in range(len(indices[0]))
        ]
    
    def save(self, file: str = "memory/vector_db.index"):
        """Speichere die Vektordatenbank."""
        faiss.write_index(self.index, file)
    
    def load(self, file: str = "memory/vector_db.index"):
        """Lade die Vektordatenbank."""
        self.index = faiss.read_index(file)
