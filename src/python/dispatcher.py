# dispatcher.py
from datetime import datetime
import logging
from handlers import (
    handle_move_block,
    handle_get_block_color,
    handle_check_occupancy
)

method_router = {
    "moveBlock": handle_move_block,
    "getBlockColor": handle_get_block_color,
    "checkOccupancy": handle_check_occupancy,
}

def dispatch_direct_method(method_name: str, payload: dict) -> dict:
    command_id = payload.get("commandId", "unknown")
    parameters = payload.get("parameters", {})
    timestamp = datetime.utcnow().isoformat()

    handler = method_router.get(method_name)
    if not handler:
        return {
            "status": 404,
            "commandId": command_id,
            "timestamp": timestamp,
            "error": {
                "message": f"Unknown method: {method_name}",
                "code": "METHOD_NOT_FOUND"
            }
        }

    try:
        result = handler(parameters)
        return {
            "status": 200,
            "commandId": command_id,
            "timestamp": datetime.utcnow().isoformat(),
            "result": result
        }
    except Exception as e:
        logging.exception("Handler exception")
        return {
            "status": 500,
            "commandId": command_id,
            "timestamp": datetime.utcnow().isoformat(),
            "error": {
                "message": str(e),
                "code": "HANDLER_EXCEPTION"
            }
        }