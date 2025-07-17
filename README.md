# xARM IoT Edge Bridge

A Python-based edge application that bridges an Arduino-powered robotic arm (xARM) to Azure IoT Hub.  
It handles Azure Direct Method calls, translates them into serial primitives for the xARM, maintains a local digital twin of block positions, and publishes reported properties back to IoT Hub. Perfect for a live Industrial IoT demo using Microsoft Fabric.

---

## Table of Contents

- [Overview](#overview)  
- [Architecture](#architecture)  
- [File Structure](#file-structure)  
- [Prerequisites](#prerequisites)  
- [Installation](#installation)  
- [Configuration](#configuration)  
- [Running the Application](#running-the-application)  
- [Supported Direct Methods](#supported-direct-methods)  
- [Module Guide](#module-guide)  
- [Extending & Adding Handlers](#extending--adding-handlers)  
- [Contributing](#contributing)  
- [License](#license)  

---

## Overview

This repository contains a modular Python application that:  
- Listens for **Direct Method** calls from Azure IoT Hub  
- Routes each call to a dedicated handler  
- Sends serial commands to an Arduino-based xARM  
- Maintains an in-memory digital twin of block positions  
- Updates the IoT Hub Device Twin with reported properties  

It’s designed for a hands-on Industrial IoT demo using Azure IoT Hub and Microsoft Fabric (Eventhouse + KQL dashboards).

---

## Architecture

```
┌──────────────┐     Direct Method        ┌─────────────┐
│ Azure IoT    │ ────────────────────────>│  main.py    │
│ Hub          │                          │  (edge app) │
└──────────────┘                          └─────┬───────┘
                                                │
                                          dispatch_direct_method()
                                                │
                                    ┌───────────┴───────────┐
                                    │      dispatcher.py    │
                                    └───────────┬───────────┘
                                                │
                            ┌───────────────────┴──────────────────┐
                            │   handlers/*.py  (method logic)      │
                            └────┬────┬─────────┬──────────┬───────┘
                                 │    │         │          │
                ┌────────────────┘    │         │          │
                │                     │         │          │
         ┌──────▼───────┐      ┌───────▼──────┐ │   ┌──────▼───────┐
         │ xarm_serial  │      │  twin.py     │ │   │ twin_cloud   │
         │ (.Serial I/O)│      │ (local state)│ │   │ (Azure patch)│
         └──────────────┘      └──────────────┘ │   └──────────────┘
                                                ▼
                                         Azure IoT Hub
                                      (Reported Properties)
```

---

## File Structure

```
/iot_xarm_app
│
├── main.py              # Entry point & IoT Hub method binding
├── config.py            # Serial port, IoT Hub conn string
├── azure_client.py      # Singleton IoT Hub client
├── dispatcher.py        # Routes methodName → handler
├── xarm_serial.py       # Serial primitives for xARM
├── twin.py              # In-memory digital twin logic
├── twin_cloud.py        # Patches reported properties to IoT Hub
└── handlers/
    ├── __init__.py
    ├── move_block.py        # handle_move_block()
    ├── get_block_color.py   # handle_get_block_color()
    └── check_occupancy.py   # handle_check_occupancy()
```

---

## Prerequisites

- Python 3.9 or higher  
- Azure IoT Device SDK for Python  
- PySerial  
- An Arduino Uno R3 running the xARM sketch  

---

## Installation

1. Clone this repo:
   ```bash
   git clone https://github.com/your-org/iot_xarm_app.git
   cd iot_xarm_app
   ```

2. Create & activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate      # Linux / macOS
   venv\Scripts\activate         # Windows
   ```

3. Install dependencies:
   ```bash
   pip install azure-iot-device pyserial
   ```

---

## Configuration

1. Open `config.py` and set your values:
   ```python
   SERIAL_PORT       = "COM3"     # or "/dev/ttyUSB0"
   BAUD_RATE         = 9600
   CONNECTION_STRING = "HostName=…;DeviceId=…;SharedAccessKey=…"
   ```

2. Verify your Arduino is connected & running the xARM sketch.

---

## Running the Application

```bash
python main.py
```

- The edge app will connect to IoT Hub, listen for Direct Methods, and process them in real time.  
- Use Azure CLI or Azure Portal to invoke methods and inspect the Device Twin.

---

## Supported Direct Methods

| methodName       | parameters                             | Description                                    |
|------------------|----------------------------------------|------------------------------------------------|
| `moveBlock`      | `sourcePoint` (int), `targetPoint` (int) | Grips a block at `sourcePoint`, places at `targetPoint`. |
| `getBlockColor`  | `point` (int)                           | Returns the color of the block at `point`.     |
| `checkOccupancy` | `point` (int)                           | Returns whether a block is present at `point`. |

**Request Envelope**  
```json
{
  "methodName": "moveBlock",
  "responseTimeoutInSeconds": 200,
  "payload": {
    "commandId": "cmd_0001",
    "timestamp": "2025-07-17T14:00:00Z",
    "parameters": {
      "sourcePoint": 2,
      "targetPoint": 5
    }
  }
}
```

**Standardized Response**  
```json
{
  "status": 200,
  "commandId": "cmd_0001",
  "timestamp": "2025-07-17T14:00:02Z",
  "result": {
    "success": true,
    "details": "Block moved from point 2 to 5",
    "blockColor": "blue"
  }
}
```

---

## Module Guide

- **`main.py`**  
  Binds the IoT Hub client’s direct-method callback to `dispatcher`.

- **`dispatcher.py`**  
  Routes `methodName` to the correct `handle_*` function and wraps its response.

- **`handlers/`**  
  Contains one file per method. Each exports `handle_<methodName>()`.

- **`xarm_serial.py`**  
  Low-level Serial I/O: `grip_block()`, `place_block()`, etc.

- **`twin.py`**  
  In-memory digital twin; `update_point_state()`, `get_twin_snapshot()`.

- **`twin_cloud.py`**  
  Packs `twin.get_twin_snapshot()` into a reported-properties JSON and calls `client.patch_twin_reported_properties()`.

- **`azure_client.py`**  
  Creates a singleton IoT Hub client used by both `main.py` and `twin_cloud.py`.

---

## Extending & Adding Handlers

1. Create a new handler file under `handlers/`, e.g. `handlers/your_method.py`.
2. Define `def handle_your_method(params: dict) -> dict:`.
3. Import and register it in `handlers/__init__.py`.
4. Add the `"yourMethod"` key to `method_router` in `dispatcher.py`.

---

## Contributing

1. Fork the repo.  
2. Create a feature branch: `git checkout -b feature/YourFeature`.  
3. Commit your changes and push: `git push origin feature/YourFeature`.  
4. Open a Pull Request—describe your changes and link any related issues.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
```
