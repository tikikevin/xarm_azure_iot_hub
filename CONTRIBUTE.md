Here’s a **clear, repeatable checklist** broken into two parts—so every time you add a new Arduino primitive or expose a new direct-method to IoT Hub, you’ll know exactly what to touch and where.

---

## 1) Adding a New Arduino Primitive

These are the steps to add a new low-level command in your Arduino sketch and make it callable from Python.

1. **Update the Arduino Sketch**  
   - Add a new `if`/`else if` branch in your `loop()` to recognize the new command string.  
   - Implement the hardware logic (move servos, read sensor, etc.).  
   - `Serial.println(...)` a JSON-style or key/value response.  
   - Example:
     ```cpp
     else if (command == "SCAN_ALL_POINTS") {
       int distances[6] = {readSonar(), /* ... */};
       // send back a simple CSV or JSON-like
       Serial.print("SCAN_RESULT:");
       for (int i=0; i<6; i++) {
         Serial.print(distances[i]);
         if (i<5) Serial.print(",");
       }
       Serial.println();
     }
     ```

2. **Expose a Python Wrapper in `xarm_serial.py`**  
   - Add a function that sends your new command and parses the response.
   - Example:
     ```python
     def scan_all_points():
         ser.write(b"SCAN_ALL_POINTS\n")
         line = ser.readline().decode().strip()
         # e.g. line == "SCAN_RESULT:120,130,110,..." 
         values = line.split(":")[1].split(",")
         return [int(v) for v in values]
     ```

3. **(Optional) Update Local Twin in `twin.py`**  
   - If the new primitive affects your digital twin state, add a helper:
     ```python
     def update_sonar_scan(scan_list):
         for idx, dist in enumerate(scan_list, start=4):
             update_point_state(idx, sonar_distance=dist)
     ```

4. **Test the Serial Call**  
   - Fire up a Python REPL in your project root:  
     ```bash
     $ python
     >>> from xarm_serial import scan_all_points
     >>> scan_all_points()
     [120, 130, 110, 90, 200, 210]
     ```

---

## 2) Exposing a New Direct Method

Once your Arduino primitive is in place, wrap it in a **handler** and wire it into IoT Hub.

1. **Create a Handler Module**  
   - In `handlers/`, add `scan_points.py` (or a descriptive name).  
   - Define `handle_scan_points(params: dict) -> dict`.  
   - Call your `xarm_serial.scan_all_points()` and any twin updates:
     ```python
     from xarm_serial import scan_all_points
     from twin import update_sonar_scan

     def handle_scan_points(params):
         scan = scan_all_points()
         update_sonar_scan(scan)
         return {"success": True, "scan": scan}
     ```

2. **Export the Handler**  
   - In `handlers/__init__.py`, add:
     ```python
     from .scan_points import handle_scan_points
     ```

3. **Register in `dispatcher.py`**  
   - In your `method_router` dict:
     ```python
     from handlers import handle_scan_points

     method_router = {
         # … existing routes …
         "scanPoints": handle_scan_points,
     }
     ```

4. **Update the README**  
   - Under **Supported Direct Methods**, add an entry:
     ```md
     | `scanPoints`    | – (no params)                          | Returns an array of sonar readings for points 4–9. |
     ```
   - Add JSON examples for request/response.

5. **Deploy & Test**  
   - Restart your edge app:  
     ```bash
     python main.py
     ```
   - In Azure CLI / Portal, invoke the method:
     ```bash
     az iot hub invoke-device-method \
       --hub-name MyHub \
       --device-id xARM \
       --method-name scanPoints \
       --method-payload "{}"
     ```
   - Verify the JSON response and that your Device Twin reported properties reflect the update.

---

### 🎯 Recap: Your End-to-End Flow for Each New Feature

1. **Arduino sketch** → add primitive command & response  
2. **xarm_serial.py** → add Python wrapper  
3. **(twin.py)** → add any needed state helpers  
4. **handlers/** → create `handle_<feature>()`  
5. **handlers/__init__.py** → export it  
6. **dispatcher.py** → map `"featureName"` → handler  
7. **README.md** → document request/response schema  
8. **Deploy & Test** → edge app + Azure direct method  

