"""Lights the LEDs on the game board. Talks to arduino/board/board.ino.

    python board.py   # light each hole in turn to check the wiring
"""
import time

import serial
import serial.tools.list_ports

PORT = "auto"   # "auto" finds the Arduino, or a path like "/dev/cu.usbmodem31101"


def connect(port=PORT):
    if port == "auto":
        found = [p.device for p in serial.tools.list_ports.comports()
                 if "usbmodem" in p.device or "usbserial" in p.device]
        if not found:
            raise SystemExit("No Arduino found. Plug it in (ls /dev/cu.*).")
        if len(found) > 1:
            raise SystemExit(f"More than one Arduino: {found}. Set PORT at the top to the board one.")
        port = found[0]
    conn = serial.Serial(port, 9600)
    time.sleep(2)   # Arduino restarts when connected, wait for it
    return conn


def light(conn, hole):
    """Turn on one hole's LED (0-8). The others go off."""
    conn.write(str(hole).encode())


def off(conn):
    """Turn all LEDs off."""
    conn.write(b"x")


if __name__ == "__main__":
    conn = connect()
    for hole in range(9):
        print("hole", hole)
        light(conn, hole)
        time.sleep(0.5)
    off(conn)
