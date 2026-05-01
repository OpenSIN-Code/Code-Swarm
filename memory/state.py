from typing import TypedDict, List, Dict, Any

class MemoryState(TypedDict):
    """State für Memory Layer."""
    vectors: List[Dict[str, Any]]
    context: Dict[str, Any]
    history: List[Dict[str, Any]]
    feedback: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
