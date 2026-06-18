# Arduino Serial Command Reference

This document describes all serial commands accepted by the xARM Arduino firmware (`xARM_Handler.ino`). These commands are sent from the Python edge application over a 9600 baud serial connection.

---

## Communication Protocol

| Parameter | Value |
|-----------|-------|
| Baud Rate | 9600 |
| Line Ending | `\n` (newline) |
| Encoding | UTF-8 |
| Response Format | `<command> <args>: <result>` |

Commands are sent as plain text strings terminated by a newline character. The Arduino reads until `\n`, trims whitespace, parses the command, executes it, and responds with a single-line result on the same serial port.

---

## Commands

### `get_block <position>`

**Purpose:** Pick up (grip) a block at the specified grid position.

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| `position` | int | 1–9 | Grid position to pick up from |

**Serial message:** `get_block 3\n`

**Response:** `get_block 3: true`

**Behavior:**
- Moves the arm to the specified position
- Closes the gripper to grab the block
- Returns the arm to a neutral carrying position
- Maps to action groups 27–35 internally (position + 26)

---

### `put_block <position>`

**Purpose:** Place the currently held block at the specified grid position.

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| `position` | int | 1–9 | Grid position to place the block |

**Serial message:** `put_block 7\n`

**Response:** `put_block 7: true`

**Behavior:**
- Moves the arm to the target position
- Opens the gripper to release the block
- Returns the arm to a neutral position
- Maps to action groups 36–44 internally (position + 35)

---

### `get_color`

**Purpose:** Read the color of the block currently positioned over the color sensor (APDS9960).

| Parameter | Type | Description |
|-----------|------|-------------|
| *(none)* | — | No parameters required |

**Serial message:** `get_color\n`

**Response:** `get_color <color> : <color>`

**Possible color values:** `red`, `green`, `blue`, `unknown`

**Behavior:**
- Reads RGB values from the APDS9960 color/proximity sensor
- Determines dominant color channel
- Returns the detected color name

**Note:** The block must be positioned over the sensor (typically via a holding position) before calling this command.

---

### `holding_block`

**Purpose:** Check whether the arm is currently gripping a block.

| Parameter | Type | Description |
|-----------|------|-------------|
| *(none)* | — | No parameters required |

**Serial message:** `holding_block\n`

**Response:** `holding_block: true` or `holding_block: false`

**Behavior:**
1. Moves the arm to a block-detection position (action group 25)
2. Reads the photosensitive sensor (analog pin A2)
3. If brightness < 15% (block is blocking light), returns `true`
4. If holding a block, retrieves it back from detection position (action group 26)

---

### `block_exists <position>`

**Purpose:** Check whether a block is present at a specific grid position using limit switches.

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| `position` | int | 1–3 | Grid position to check (only positions 1–3 are wired) |

**Serial message:** `block_exists 2\n`

**Response:** `block_exists 2 : true` or `block_exists 2 : false`

**Behavior:**
- Reads digital pins 3, 4, or 5 (mapped to positions 1, 2, 3)
- Returns `true` if the pin reads HIGH (block present)
- Positions 4–9 always return `false` (no sensors wired)

---

### `scan_row`

**Purpose:** Use the ultrasonic distance sensor to detect which position in the far row (4–6) contains a block.

| Parameter | Type | Description |
|-----------|------|-------------|
| *(none)* | — | No parameters required |

**Serial message:** `scan_row\n`

**Response:** `scan_row <position> : <position>`

**Possible return values:**
| Distance (mm) | Mapped Position |
|---------------|----------------|
| < 100 | 4 |
| 100–199 | 5 |
| 200–299 | 6 |
| ≥ 300 | -1 (no block detected) |

**Behavior:**
- Reads distance from I2C ultrasonic sensor (address `0x77`)
- Maps distance ranges to grid positions
- Returns `-1` if no block is within detectable range

---

## Grid Layout

The xARM operates on a 3×3 grid (positions 1–9):

```
┌─────────────────────────────┐
│  Far row (ultrasonic scan)  │
│   [4]    [5]    [6]         │
│                             │
│  Near row (limit switches)  │
│   [1]    [2]    [3]         │
│                             │
│  Storage row                │
│   [7]    [8]    [9]         │
└─────────────────────────────┘
        ↑ ARM BASE ↑
```

- **Positions 1–3:** Near row with digital presence sensors (pins 3, 4, 5)
- **Positions 4–6:** Far row scanned by ultrasonic sensor
- **Positions 7–9:** Storage/destination positions

---

## Action Group Mapping

The Arduino firmware uses pre-programmed servo action groups stored on the LewanSoul/LobotServoController board:

| Action Group ID | Function |
|----------------|----------|
| 0 | Home position |
| 13–24 | Legacy compound moves (point-to-point) |
| 25 | Move arm to block detection (holding check) position |
| 26 | Retrieve arm from block detection position |
| 27–35 | Get (pick up) block from positions 1–9 |
| 36–44 | Put (place) block at positions 1–9 |

---

## Error Handling

If an unrecognized command is sent, the Arduino responds with:

```
command unknown
```

The Python edge application implements a 10-second timeout when waiting for Arduino responses. If no response is received, it returns a timeout warning.

---

## Hardware Components

| Component | Connection | Purpose |
|-----------|-----------|---------|
| LobotServoController | SoftwareSerial (pins 8 TX, 9 RX) | Drives arm servos via action groups |
| APDS9960 | SoftWire I2C (pins 6 SDA, 7 SCL) | Color detection sensor |
| Ultrasonic sensor | I2C address `0x77` | Distance measurement for row scanning |
| Photosensitive sensor | Analog pin A2 | Block holding detection |
| Limit switches | Digital pins 3, 4, 5 | Block presence at positions 1–3 |
| OLED Display | *(via DisplayUI)* | Shows last command/response status |
