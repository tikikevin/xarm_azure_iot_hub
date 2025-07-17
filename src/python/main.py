# main.py
import logging
from azure.iot.device import MethodResponse
from azure_client import client as device_client
from dispatcher import dispatch_direct_method
from twin_cloud import sync_reported_properties
from config import CONNECTION_STRING

logging.basicConfig(level=logging.INFO)

# Register your method handler
def method_request_handler(method_request):
    logging.info(f"Received direct method: {method_request.name}")
    
    # 1) Dispatch to your Python handler
    response_payload = dispatch_direct_method(
        method_name=method_request.name,
        payload=method_request.payload
    )
    
    # 2) Reply synchronously to IoT Hub
    device_client.send_method_response(
        MethodResponse(
            method_request.request_id,
            response_payload,
            status=response_payload.get("status", 500)
        )
    )
    
    # 3) Update the Device Twin with new local state
    sync_reported_properties()

# hook up and run
device_client.on_method_request_received = method_request_handler

print("Listening for direct methods…")
device_client.connect()
try:
    while True:
        pass
except KeyboardInterrupt:
    print("Exiting")
    device_client.disconnect()