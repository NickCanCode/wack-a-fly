"""Moves the arm to a hole, taps it, and checks the magnet sensor on the tip.
Talks to arduino/arm/arm.ino.

    python arm.py 4   # hit hole 4
    python arm.py     # hit every hole, 0 to 8
"""
import sys
import time

import serial
import serial.tools.list_ports

PORT = "auto"     # "auto" finds the Arduino, or a path like "/dev/cu.usbmodem31201"
UP = 90           # arm angle when raised
HOME = (90, 90)   # base, arm angles when resting

# (base angle, arm angle when down) for holes 0-8.
# These are guesses: find the real ones by typing M commands (like M55,40) in the Serial Monitor.
HOLES = [
    (20, 40), (38, 40), (55, 40),
    (72, 40), (90, 40), (108, 40),
    (125, 40), (142, 40), (160, 40),
]


def connect(port=PORT):
    if port == "auto":
        found = [p.device for p in serial.tools.list_ports.comports()
                 if "usbmodem" in p.device or "usbserial" in p.device]
        if not found:
            raise SystemExit("No Arduino found. Plug it in (ls /dev/cu.*).")
        if len(found) > 1:
            raise SystemExit(f"More than one Arduino: {found}. Set PORT at the top to the arm one.")
        port = found[0]
    conn = serial.Serial(port, 9600, timeout=10)
    time.sleep(2)   # Arduino restarts when connected, wait for it
    return conn


def move(conn, base, arm):
    """Move both servos and wait until the arm gets there."""
    conn.write(f"M{base},{arm}\n".encode())
    if conn.readline().decode().strip() != "OK":
        raise TimeoutError("Arm didn't answer. Is arduino/arm/arm.ino uploaded?")


def magnet(conn):
    """True if the magnet sensor on the tip feels a magnet."""
    conn.write(b"R")
    return conn.readline().decode().strip() == "1"


def hit(conn, hole):
    """Go above the hole, tap down, check the magnet, lift back up, go home."""
    base, down = HOLES[hole]
    move(conn, base, UP)
    move(conn, base, down)
    found = magnet(conn)
    move(conn, base, UP)
    move(conn, *HOME)
    return found


if __name__ == "__main__":
    conn = connect()
    holes = [int(sys.argv[1])] if len(sys.argv) > 1 else range(9)
    for hole in holes:
        start = time.time()
        found = hit(conn, hole)
        print(f"hole {hole}: {'magnet' if found else 'nothing'} ({time.time() - start:.1f}s)")
