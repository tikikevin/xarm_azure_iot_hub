# xarm_serial.py
import serial
from config import SERIAL_PORT, BAUD_RATE

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)

def grip_block(point: int) -> str:
    ser.write(f"GRIP BLOCK POINT {point}\n".encode('utf-8'))
    response = ser.readline().decode('utf-8').strip()
    if response != "OK":
        raise Exception(f"Failed to grip block at point {point}")
    else:
        print(f"Block gripped at point {point}")
    print(ser.readline().decode('utf-8').strip())
    return response

def place_block(point: int) -> str:
    ser.write(f"PLACE BLOCK POINT {point}\n".encode('utf-8'))
    response = ser.readline().decode('utf-8').strip()
    if response != "OK":
        raise Exception(f"Failed to place block at point {point}")
    else:
        print(f"Block placed at point {point}")
    print(ser.readline().decode('utf-8').strip())
    return response

def check_occupancy(point: int) -> str:
    ser.write(f"CHECK OCCUPANCY POINT {point}\n".encode('utf-8'))
    response = ser.readline().decode('utf-8').strip()
    return response == "OCCUPIED"

def get_block_color(point: int) -> str:
    ser.write(f"GET BLOCK COLOR POINT {point}\n".encode('utf-8'))
    response = ser.readline().decode('utf-8').strip()
    return response if response else "unknown"

def close_serial():
    if ser.is_open:
        ser.close()
        print("Serial connection closed.")
    else:
        print("Serial connection was already closed.")
