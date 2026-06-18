import serial
import asyncio
import json
import time
from helper import SERIAL_PORT, BAUD_RATE, CONNECTION_STRING
from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import Message, MethodResponse
from twin_manager import TwinManager

ser = None  # Global variable for serial connection

async def get_serial() -> serial.Serial:
    """
    Asynchronously attempts to establish a serial connection with the specified port using exponential backoff.

    This function repeatedly tries to connect to a serial port defined by the global variable `SERIAL_PORT` 
    with the baud rate specified by `BAUD_RATE`. If the connection fails, it waits for an exponentially 
    increasing delay (starting at 2 seconds, up to a maximum of 30 seconds) before retrying. The process 
    continues until a successful connection is made (i.e., `ser` is not None and is open).

    Returns:
        serial.Serial: An open serial connection object.

    Raises:
        None: All exceptions related to serial connection are handled internally with retries.

    Side Effects:
        - Modifies the global variable `ser` to hold the connected serial object.
        - Prints connection status and errors to the console.
        - Waits asynchronously between retries.

    Note:
        This function is designed to be used in an asynchronous context (i.e., must be awaited).
    """
    global ser
    delay = 2
    while ser is None or not ser.is_open:
        try:
            print(f"🔄 Attempting to connect to serial port {SERIAL_PORT}...")
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
            print(f"🔗 Serial connected on {SERIAL_PORT}")
        except serial.SerialException as e:
            print(f"❌ Serial connection failed: {e}")
            print(f"⏳ Retrying in {delay} seconds...")
            await asyncio.sleep(delay)
            delay = min(delay * 2, 30)  # exponential backoff up to 30s
    return ser

# Function to send telemetry data from Arduino to Azure IoT Hub
async def send_telemetry(client, serial_lock):
    """
    Continuously reads telemetry data from a serial connection and sends it to a client.

    Args:
        client: An asynchronous client object with a `send_message` coroutine method for transmitting telemetry data.
        serial_lock: An asyncio-compatible lock to ensure exclusive access to the serial connection.

    Behavior:
        - Acquires the serial lock to safely access the serial port.
        - Attempts to establish a serial connection using `get_serial()`.
        - If data is available (`in_waiting`), reads a line from the serial port, decodes it, and sends it to the client.
        - Handles and logs exceptions, closes the serial connection on error, and resets the global serial object.
        - Repeats the process every second.

    Exceptions:
        - Catches and logs all exceptions during telemetry reading or sending.
        - Ensures the serial connection is closed and cleaned up on error.

    Note:
        This function is designed to run indefinitely as an asyncio task.
    """
    while True:
        try:
            async with serial_lock:
                ser_conn = await get_serial()
                if ser_conn.in_waiting:
                    raw_data = ser_conn.readline().decode('utf-8').strip()
                    if raw_data:
                        print(f"📡 Sending from Arduino: {raw_data}")
                        await client.send_message(raw_data)
        except Exception as e:
            print(f"⚠️ Telemetry error: {e}")
            if ser_conn: ser_conn.close()
            global ser
            ser = None
        await asyncio.sleep(1)


async def receive_c2d_messages(client, serial_lock):
    """
    Asynchronously receives Cloud-to-Device (C2D) messages from Azure IoT Hub and forwards them to a serial device.
    This function continuously listens for incoming C2D messages from the provided Azure IoT client. Upon receiving a message,
    it decodes the message body and sends it to a connected serial device (e.g., Arduino) using a specified protocol.
    The function also reads and prints any response from the serial device. Serial access is synchronized using an asyncio lock
    to prevent concurrent access. In case of errors, the serial connection is closed and reset.
    Args:
        client: An asynchronous Azure IoT client instance with a `receive_message` coroutine method.
        serial_lock (asyncio.Lock): An asyncio lock to synchronize access to the serial connection.
    Raises:
        None. All exceptions are caught and logged within the function.
    Note:
        This function runs an infinite loop and is intended to be run as an asyncio task.
    """
    while True:
        try:
            message = await client.receive_message()
            if message:
                msg_body = message.data.decode()
                print(f"📨 Received C2D message: {msg_body}")

                async with serial_lock:
                    ser_conn = await get_serial()
                    serial_msg = f"c2d:{msg_body}\n"
                    ser_conn.write(serial_msg.encode())

                    if ser_conn.in_waiting:
                        arduino_response = ser_conn.readline().decode('utf-8').strip()
                        print(f"🤖 Arduino response: {arduino_response}")
        except Exception as e:
            print(f"⚠️ C2D error: {e}")
            if ser_conn: ser_conn.close()
            global ser
            ser = None
        await asyncio.sleep(0.5)  # Poll every 500ms


async def handle_methods(client, serial_lock, twin_manager: TwinManager):
    """
    Handles direct method requests from Azure IoT Hub, sends the requested command to an Arduino device via serial communication,
    and returns the Arduino's response back to Azure IoT Hub. Updates the digital twin after each command.
    Args:
        client: The Azure IoT client instance used to receive and respond to method requests.
        serial_lock: An asyncio-compatible lock to ensure exclusive access to the serial connection.
        twin_manager: TwinManager instance for updating reported properties.
    Returns:
        None. The function runs indefinitely, processing incoming method requests.
    """
    while True:
        method_request = await client.receive_method_request()
        method_name = method_request.name
        payload = method_request.payload

        print(f"⚙️ Received direct method: {method_name}, payload: {payload}")

        # Mark arm as busy
        twin_manager.set_arm_state("busy")

        try:
            async with serial_lock:
                ser_conn = await get_serial()
                serial_msg = f"{method_name}:{payload}\n"
                ser_conn.write(serial_msg.encode())

                # Wait up to 30 seconds for a response — robot arm movements
                # can take 10-20+ seconds for physical actions like get_block
                timeout = 30
                start_time = time.time()
                arduino_response = ""

                while time.time() - start_time < timeout:
                    if ser_conn.in_waiting:
                        arduino_response = ser_conn.readline().decode('utf-8').strip()
                        if arduino_response:
                            break
                    await asyncio.sleep(0.1)  # avoid busy waiting

                if not arduino_response:
                    arduino_response = "⚠️ No response from Arduino within timeout."

                print(f"📬 Arduino replied: {arduino_response}")

            status = 200
            response_payload = {"result": arduino_response}

            # Update twin state based on command result
            twin_manager.update_from_command(method_name, str(payload) if payload else "", arduino_response)

        except Exception as e:
            print(f"❌ Method handler error: {e}")
            if ser_conn: ser_conn.close()
            global ser
            ser = None
            status = 500
            response_payload = {"error": str(e)}

        # Mark arm as idle and push twin update
        twin_manager.set_arm_state("idle")
        await twin_manager.push_twin_update()

        method_response = MethodResponse.create_from_method_request(
            method_request, status, response_payload
        )
        await client.send_method_response(method_response)


async def main():
    """
    Main entry point for the application.
    Initializes the Azure IoT Hub device client, digital twin manager,
    and launches all concurrent tasks: telemetry, C2D messages, direct methods,
    and periodic sensor polling.
    """
    # Create IoT Hub device client
    device_client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
    print("🔌 Connecting to Azure IoT Hub...")
    await device_client.connect()
    print("✅ Connected! Listening & sending telemetry...")

    # Create serial lock in the correct event loop context
    serial_lock = asyncio.Lock()

    # Create twin manager
    twin_mgr = TwinManager(device_client, serial_lock, get_serial)

    # Register desired properties handler (allows cloud to adjust poll interval)
    device_client.on_twin_desired_properties_patch_received = twin_mgr.handle_desired_properties

    # Run all handlers concurrently
    await asyncio.gather(
        send_telemetry(device_client, serial_lock),
        receive_c2d_messages(device_client, serial_lock),
        handle_methods(device_client, serial_lock, twin_mgr),
        twin_mgr.run_periodic_poll(),
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Stopping client...")