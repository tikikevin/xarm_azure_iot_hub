# handlers/check_occupancy.py
def handle_check_occupancy(params: dict) -> dict:
    point = params.get("point")
    if point is None:
        raise ValueError("Missing point")

    # Replace with serial logic
    is_occupied = point in [1, 3]  # Mock data

    return {
        "success": True,
        "occupied": is_occupied
    }