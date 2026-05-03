from typing import TypedDict, List, Dict, Any

class OpenCodeState(TypedDict):
    """State für das LangGraph-Agenten-System."""
    task: str
    research: List[Dict[str, Any]]
    plans: List[Dict[str, Any]]
    validated_plan: Dict[str, Any]
    execution_log: List[Dict[str, Any]]
    memory: Dict[str, Any]  # Vektordatenbank
    errors: List[Dict[str, Any]]  # Error Tracking
    feedback: List[Dict[str, Any]]  # Feedback-Loops
    metrics: Dict[str, Any]  # Benchmark-Metriken
