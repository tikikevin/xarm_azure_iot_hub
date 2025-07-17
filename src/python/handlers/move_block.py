# handlers/move_block.py
from xarm_serial import grip_block, place_block
from twin import update_point_state

def handle_move_block(params: dict) -> dict:
    source = params.get("sourcePoint")
    target = params.get("targetPoint")

    if source is None or target is None:
        raise ValueError("Missing sourcePoint or targetPoint")

    grip_block(source)
    place_block(target)

    update_point_state(source, occupied=False)
    update_point_state(target, occupied=True)

    return {
        "success": True,
        "details": f"Block moved from point {source} to {target}",
        "blockColor": "blue"  # if sensor data is available
    }