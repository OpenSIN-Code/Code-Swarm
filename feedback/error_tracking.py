import json
from pathlib import Path
from typing import List, Dict, Any

class ErrorTracker:
    """Error Tracking für Feedback-Loops."""
    
    def __init__(self, file: str = "feedback/errors.json"):
        self.errors = []
        self.file = Path(file)
        self.file.parent.mkdir(parents=True, exist_ok=True)
    
    def log(self, agent: str, error: str, context: Dict[str, Any], task: str = None):
        """Logge einen Fehler."""
        error_entry = {
            "timestamp": str(Path(".").resolve()),
            "agent": agent,
            "error": error,
            "context": context,
            "task": task
        }
        self.errors.append(error_entry)
        self._save()
    
    def get_errors(self, agent: str = None) -> List[Dict[str, Any]]:
        """Hole alle Fehler für einen Agenten."""
        if agent:
            return [e for e in self.errors if e["agent"] == agent]
        return self.errors
    
    def _save(self):
        """Speichere Fehler in Datei."""
        with open(self.file, "w") as f:
            json.dump(self.errors, f, indent=2)
    
    def load(self):
        """Lade Fehler aus Datei."""
        if self.file.exists():
            with open(self.file) as f:
                self.errors = json.load(f)
