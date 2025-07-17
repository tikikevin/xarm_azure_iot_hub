# twin_cloud.py
from datetime import datetime
from azure_client import client
from twin import get_twin_snapshot

def sync_reported_properties():
    """
    Push the current local twin (reported properties)
    up to Azure IoT Hub.
    """
    # build the reported properties object
    reported = {
        "points": get_twin_snapshot(),
        "lastUpdated": datetime.utcnow().isoformat()
    }
    # patch it
    client.patch_twin_reported_properties(reported)