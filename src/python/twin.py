# twin.py
from datetime import datetime

# holds per-point state
point_states = {}  

def update_point_state(point: int, **kwargs):
    """Update local twin state for a given point."""
    state = point_states.get(point, {})
    state.update(kwargs)
    state["lastUpdated"] = datetime.utcnow().isoformat()
    point_states[point] = state

def get_twin_snapshot() -> dict:
    """Return the full twin as a dict of reported props."""
    return {
        str(k): v
        for k, v in point_states.items()
    }