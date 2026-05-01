from typing import List, Dict, Any
from memory.vector_db import VectorDB
from feedback.error_tracking import ErrorTracker

class SelfImprovementLoop:
    """Self-Improvement Loop für Agenten-Systeme."""
    
    def __init__(self):
        self.vector_db = VectorDB()
        self.error_tracker = ErrorTracker()
    
    def analyze(self, agent: str, results: Dict[str, Any], context: Dict[str, Any]):
        """Analysiere Ergebnisse und verbessere Agenten."""
        # Speichere Ergebnisse in Vektordatenbank
        self.vector_db.add(results.get("vector", []), f"{agent}-results", {
            "task": context.get("task"),
            "metrics": results.get("metrics", {})
        })
        
        # Prüfe auf Fehler
        if "errors" in results:
            for error in results["errors"]:
                self.error_tracker.log(agent, error, context)
        
        # Lerne aus Feedback
        feedback = self._get_feedback(agent)
        self._improve_model(agent, feedback)
    
    def _get_feedback(self, agent: str) -> Dict[str, Any]:
        """Hole Feedback von anderen Agenten."""
        return {
            "quality": "good",
            "speed": "fast",
            "accuracy": "high"
        }
    
    def _improve_model(self, agent: str, feedback: Dict[str, Any]):
        """Verbessere das Modell basierend auf Feedback."""
        print(f"🔥 Agent {agent} verbessert sich basierend auf Feedback: {feedback}")
        # Hier könnte man z.B. Prompts anpassen oder Modelle neu trainieren
