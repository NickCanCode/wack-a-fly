"""Robot arm control: moves to one of the 9 holes, taps it, and checks the magnet sensor.

Usage:
    python arm.py calibrate   # jog the arm by hand and save a pose for each hole
    python arm.py test        # hit every saved hole in order
    python arm.py hit 4       # hit one hole

From other code:
    arm = Arm(connect())
    found = arm.hit(4)        # True if the sensor felt the magnet
"""
import json
import sys
import time
from pathlib import Path

import serial
import serial.tools.list_ports

POSES_FILE = Path(__file__).with_name("arm_poses.json")
HOME = [90, 90]     # base, arm angles when resting
UP = 90             # arm angle when raised (find yours with servo_test.ino)
NAMES = ["base", "arm"]


def connect(port="auto"):
    if port == "auto":
        found = [p.device for p in serial.tools.list_ports.comports()
                 if "usbmodem" in p.device or "usbserial" in p.device]
        if not found:
            raise SystemExit("No Arduino found. Plug it in (ls /dev/cu.*).")
        port = found[0]
    conn = serial.Serial(port, 9600, timeout=10)
    time.sleep(2)   # Arduino restarts when connected, wait for it
    return conn


class Arm:
    def __init__(self, conn):
        self.conn = conn
        self.angles = list(HOME)
        self.poses = json.loads(POSES_FILE.read_text()) if POSES_FILE.exists() else {}

    def _reply(self):
        line = self.conn.readline().decode().strip()
        if not line:
            raise TimeoutError("Arduino didn't answer. Is wack_a_fly.ino uploaded?")
        return line

    def move(self, angles):
        angles = [max(0, min(180, int(a))) for a in angles]
        self.conn.write(f"M{angles[0]},{angles[1]}\n".encode())
        self._reply()   # "OK" once the arm has arrived
        self.angles = angles

    def preset(self, n):
        """Move to preset n from the presets table in wack_a_fly.ino."""
        self.conn.write(f"P{n}\n".encode())
        self._reply()   # "OK" once the arm has arrived

    def magnet(self):
        self.conn.write(b"R")
        return self._reply() == "1"

    def home(self):
        self.move(HOME)

    def hit(self, hole):
        """Tap a hole and return True if the magnet was there."""
        down = self.poses.get(str(hole))
        if down is None:
            raise KeyError(f"No pose saved for hole {hole}. Run: python arm.py calibrate")
        above = [down[0], UP]
        self.move(above)
        self.move(down)
        found = self.magnet()
        self.move(above)
        self.home()
        return found

    def save_pose(self, hole):
        self.poses[str(hole)] = list(self.angles)
        POSES_FILE.write_text(json.dumps(self.poses, indent=2))


def calibrate(arm):
    print("Jog the arm until the tip touches a hole, then save it.")
    print("  b+10 / a-5         turn base / move arm by that many degrees")
    print("  save 4             save current angles as hole 4")
    print("  hit 4              try hitting hole 4")
    print("  home | magnet | quit")
    arm.home()
    while True:
        print("  now: " + ", ".join(f"{n} {a}" for n, a in zip(NAMES, arm.angles)),
              "| saved holes:", sorted(arm.poses, key=int) or "none")
        cmd = input("> ").strip().lower()
        try:
            if cmd in ("q", "quit"):
                break
            elif cmd == "home":
                arm.home()
            elif cmd == "magnet":
                print("  magnet!" if arm.magnet() else "  no magnet")
            elif cmd.startswith("save "):
                arm.save_pose(int(cmd.split()[1]))
            elif cmd.startswith("hit "):
                print("  magnet!" if arm.hit(int(cmd.split()[1])) else "  no magnet")
            elif cmd[:1] in ("b", "a") and len(cmd) > 1:
                angles = list(arm.angles)
                angles["ba".index(cmd[0])] += int(cmd[1:])
                arm.move(angles)
            else:
                print("  ?")
        except (ValueError, KeyError) as e:
            print("  ", e)
    arm.home()


if __name__ == "__main__":
    arm = Arm(connect())
    mode = sys.argv[1] if len(sys.argv) > 1 else "calibrate"
    if mode == "calibrate":
        calibrate(arm)
    elif mode == "test":
        for hole in sorted(arm.poses, key=int):
            start = time.time()
            found = arm.hit(int(hole))
            print(f"hole {hole}: {'magnet' if found else 'nothing'} ({time.time() - start:.2f}s)")
    elif mode == "hit":
        print("magnet" if arm.hit(int(sys.argv[2])) else "nothing")
