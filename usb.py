"""Opens the USB connection to an Arduino. Used by board.py and arm.py."""
import time

import serial
import serial.tools.list_ports


def connect(port, name, timeout=None):
    """port: "auto" finds the Arduino, or a path like "/dev/cu.usbmodem31101".
    name: "board" or "arm", so the error message says which file to fix.
    timeout: seconds to wait for an answer (None = wait forever)."""
    if port == "auto":
        found = [p.device for p in serial.tools.list_ports.comports()
                 if "usbmodem" in p.device or "usbserial" in p.device]
        if not found:
            raise SystemExit("No Arduino found. Plug it in (ls /dev/cu.*).")
        if len(found) > 1:
            raise SystemExit(f"More than one Arduino: {found}. Set PORT at the top of {name}.py to the {name} one.")
        port = found[0]
    conn = serial.Serial(port, 9600, timeout=timeout)
    time.sleep(2)   # Arduino restarts when connected, wait for it
    return conn
