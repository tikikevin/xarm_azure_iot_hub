import logging
from datetime import datetime

# Sample method router
method_router = {
    "moveBlock": handle_move_block,
    "getBlockColor": handle_get_block_color,
    "checkOccupancy": handle_check_occupancy,
    # Add more handlers as needed
}

def dispatch_direct_method(method_name: str, payload: dict) -> dict:
    command_id = payload.get("commandId", "unknown")
    timestamp = datetime.utcnow().isoformat()

    handler = method_router.get(method_name)
    if not handler:
        logging.warning(f"[{method_name}] No handler found.")
        return {
            "status": 404,
            "commandId": command_id,
            "timestamp": timestamp,
            "error": {
                "message": f"Unknown method '{method_name}'",
                "code": "METHOD_NOT_FOUND"
            }
        }

    try:
        result = handler(payload.get("parameters", {}))
        return {
            "status": 200,
            "commandId": command_id,
            "timestamp": datetime.utcnow().isoformat(),
            "result": result
        }
    except Exception as e:
        logging.exception(f"[{method_name}] Handler error.")
        return {
            "status": 500,
            "commandId": command_id,
            "timestamp": datetime.utcnow().isoformat(),
            "error": {
                "message": str(e),
                "code": "HANDLER_EXCEPTION"
            }
        }
    
def handle_move_block(params: dict) -> dict:
    source = params.get("sourcePoint")
    target = params.get("targetPoint")

    # Validate inputs
    if source is None or target is None:
        raise ValueError("Missing sourcePoint or targetPoint")

    # Here you'd send commands to xARM over serial
    # e.g., grip_block(source), place_block(target)

    # Simulate success
    return {
        "success": True,
        "details": f"Block moved from point {source} to {target}",
        "blockColor": "blue"  # if known or detected
    }

def handle_get_block_color(params: dict) -> dict:
    # Simulate reading a sensor value
    return {
        "color": "green",
        "success": True
    }

def handle_check_occupancy(params: dict) -> dict:
    point = params.get("point")
    if point is None:
        raise ValueError("Missing point")

    # Simulate sensor check
    return {
        "occupied": point in [1, 3],  # Dummy logic
        "success": True
    }


# Using the Azure IoT SDK for Python, you can register the dispatcher:
def method_request_handler(method_request):
    """
    Handles incoming direct method requests from IoT Hub.
    Args:
        method_request: An object representing the direct method request, containing
            the method name, payload, and request ID.
    Processes the method request by dispatching it to the appropriate handler based
    on the method name and payload. Constructs a response payload and sends a method
    response back to the IoT Hub with the corresponding status code.
    Returns:
        None
    """
    response_payload = dispatch_direct_method(
        method_name=method_request.name,
        payload=method_request.payload
    )

    # Extract status from response payload or default to 500
    status = response_payload.get("status", 500)
    device_client.send_method_response(
        MethodResponse(method_request.request_id, response_payload, status)
    )