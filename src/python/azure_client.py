# azure_client.py
from azure.iot.device import IoTHubDeviceClient
from config import CONNECTION_STRING

# singleton IoT Hub client
client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)