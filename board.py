"""Lights the LEDs on the game board. Talks to arduino/board/board.ino.

    python board.py   # light each hole in turn to check the wiring
"""
import time

import usb

PORT = "auto"   # "auto" finds the Arduino, or a path like "/dev/cu.usbmodem31101"


def connect(port=PORT):
    return usb.connect(port, "board")


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
