"""Digital Twin Manager — maintains and reports robot state to Azure IoT Hub.

Updates the device twin's reported properties after every command and
periodically polls passive sensors (IR positions 1-3, sonar for 4-6)
to detect manual block movements.
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Any


# Default poll interval in seconds (can be overridden via desired properties)
DEFAULT_POLL_INTERVAL = 30


class TwinManager:
    """Manages the robot's digital twin reported properties."""

    def __init__(self, device_client, serial_lock, get_serial_fn):
        self._client = device_client
        self._serial_lock = serial_lock
        self._get_serial = get_serial_fn
        self._poll_interval = DEFAULT_POLL_INTERVAL

        # Internal state
        self._grid: dict[str, dict[str, Any]] = {}
        self._holding: dict[str, Any] = {
            "status": False,
            "color": None,
            "updated": None,
        }
        self._arm_state: str = "idle"
        self._last_command: dict[str, Any] = {}

        # Initialize grid with all positions unknown
        for pos in range(1, 10):
            self._grid[str(pos)] = {
                "status": "unknown",
                "color": None,
                "updated": None,
            }

    def _now(self) -> str:
        """Current UTC timestamp as ISO string."""
        return datetime.now(timezone.utc).isoformat()

    # ------------------------------------------------------------------
    # State update methods (called after command results)
    # ------------------------------------------------------------------

    def update_from_command(self, method_name: str, payload: str, result: str) -> None:
        """Parse a command result and update internal state accordingly."""
        result_lower = result.lower()
        now = self._now()

        self._last_command = {
            "name": method_name,
            "payload": payload,
            "result": result.strip(),
            "time": now,
        }

        try:
            pos = int(payload) if payload else 0
        except (ValueError, TypeError):
            pos = 0

        if method_name == "get_block" and pos:
            if "true" in result_lower:
                # Block was picked up from this position
                self._grid[str(pos)] = {
                    "status": "empty",
                    "color": None,
                    "updated": now,
                }
                # We're now holding whatever was there
                prev_color = self._grid.get(str(pos), {}).get("color")
                self._holding = {
                    "status": True,
                    "color": prev_color,  # may be None if color wasn't known
                    "updated": now,
                }
            else:
                # get_block failed — position might be empty
                self._grid[str(pos)] = {
                    "status": "empty",
                    "color": None,
                    "updated": now,
                }

        elif method_name == "put_block" and pos:
            if "true" in result_lower:
                # Block placed at position
                self._grid[str(pos)] = {
                    "status": "occupied",
                    "color": self._holding.get("color"),
                    "updated": now,
                }
                self._holding = {
                    "status": False,
                    "color": None,
                    "updated": now,
                }

        elif method_name == "get_color":
            # Parse color from result like "get_color: red"
            for color in ("red", "green", "blue"):
                if color in result_lower:
                    self._holding["color"] = color
                    self._holding["updated"] = now
                    break

        elif method_name == "holding_block":
            if "true" in result_lower:
                self._holding["status"] = True
                self._holding["updated"] = now
            else:
                self._holding = {
                    "status": False,
                    "color": None,
                    "updated": now,
                }

        elif method_name == "block_exists" and pos:
            if "true" in result_lower:
                # Keep existing color if we knew it
                existing_color = self._grid.get(str(pos), {}).get("color")
                self._grid[str(pos)] = {
                    "status": "occupied",
                    "color": existing_color,
                    "updated": now,
                }
            else:
                self._grid[str(pos)] = {
                    "status": "empty",
                    "color": None,
                    "updated": now,
                }

        elif method_name == "scan_row":
            # Result like "scan_row: 4" or "scan_row: -1"
            scanned_pos = -1
            for token in result.split():
                try:
                    scanned_pos = int(token)
                    break
                except ValueError:
                    continue

            if scanned_pos == -1:
                # No blocks in row 4-6
                for p in range(4, 7):
                    self._grid[str(p)] = {
                        "status": "empty",
                        "color": None,
                        "updated": now,
                    }
            elif 4 <= scanned_pos <= 6:
                # Nearest block found at this position
                existing_color = self._grid.get(str(scanned_pos), {}).get("color")
                self._grid[str(scanned_pos)] = {
                    "status": "occupied",
                    "color": existing_color,
                    "updated": now,
                }
                # Positions closer to sonar are empty
                for p in range(4, scanned_pos):
                    self._grid[str(p)] = {
                        "status": "empty",
                        "color": None,
                        "updated": now,
                    }

    def set_arm_state(self, state: str) -> None:
        """Set arm state: 'idle' or 'busy'."""
        self._arm_state = state

    # ------------------------------------------------------------------
    # Twin reporting
    # ------------------------------------------------------------------

    def _build_reported_properties(self) -> dict[str, Any]:
        """Build the full reported properties payload."""
        return {
            "grid": self._grid,
            "holding": self._holding,
            "arm_state": self._arm_state,
            "last_command": self._last_command,
            "last_sensor_poll": None,  # updated by poll_sensors
            "poll_interval_seconds": self._poll_interval,
        }

    async def push_twin_update(self) -> None:
        """Push current state to IoT Hub as reported properties."""
        reported = self._build_reported_properties()
        try:
            await self._client.patch_twin_reported_properties(reported)
            print(f"🔄 Twin updated: holding={self._holding['status']}, arm={self._arm_state}")
        except Exception as e:
            print(f"⚠️ Twin update failed: {e}")

    # ------------------------------------------------------------------
    # Periodic sensor polling
    # ------------------------------------------------------------------

    async def _send_serial_command(self, command: str) -> str:
        """Send a command to Arduino and wait for response."""
        async with self._serial_lock:
            ser_conn = await self._get_serial()
            ser_conn.write(f"{command}\n".encode())

            timeout = 10
            start_time = time.time()
            response = ""

            while time.time() - start_time < timeout:
                if ser_conn.in_waiting:
                    response = ser_conn.readline().decode('utf-8').strip()
                    if response:
                        break
                await asyncio.sleep(0.1)

        return response

    async def poll_sensors(self) -> None:
        """Poll all passive sensors and update grid state."""
        now = self._now()

        # Poll IR sensors for positions 1, 2, 3
        for pos in range(1, 4):
            response = await self._send_serial_command(f"block_exists:{pos}")
            if response:
                self.update_from_command("block_exists", str(pos), response)

        # Poll sonar for row 2 (positions 4-6)
        response = await self._send_serial_command("scan_row:")
        if response:
            self.update_from_command("scan_row", "", response)

        # Update the poll timestamp
        reported = self._build_reported_properties()
        reported["last_sensor_poll"] = now
        try:
            await self._client.patch_twin_reported_properties(reported)
            print(f"📡 Sensor poll complete: {now}")
        except Exception as e:
            print(f"⚠️ Sensor poll twin update failed: {e}")

    async def run_periodic_poll(self) -> None:
        """Run sensor polling on a loop. Respects poll_interval from desired properties."""
        # Wait a few seconds on startup for serial to be ready
        await asyncio.sleep(5)

        while True:
            # Only poll when arm is idle
            if self._arm_state == "idle":
                try:
                    await self.poll_sensors()
                except Exception as e:
                    print(f"⚠️ Sensor poll error: {e}")

            await asyncio.sleep(self._poll_interval)

    # ------------------------------------------------------------------
    # Desired properties handler
    # ------------------------------------------------------------------

    async def handle_desired_properties(self, patch: dict) -> None:
        """Handle desired property updates from the cloud."""
        if "poll_interval_seconds" in patch:
            new_interval = patch["poll_interval_seconds"]
            if isinstance(new_interval, (int, float)) and new_interval >= 5:
                self._poll_interval = int(new_interval)
                print(f"⚙️ Poll interval updated to {self._poll_interval}s")
