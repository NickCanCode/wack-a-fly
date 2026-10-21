# Wack-a-Fly

A whack-a-mole board where a robot arm does the whacking. A camera watches the board, and one of two models decides which hole to hit:

- **SNN** (spiking neural network): a neuromorphic model that only reacts to parts of the picture that change.
- **YOLO**: a normal object detector that looks at the whole picture every frame.

The two take turns, and their scores and speed are compared on screen.

Neuromorphic Computing class project.

## Hardware

- **Board Arduino** (Uno): 9 LEDs on pins 2-10, one per hole.
- **Arm Arduino** (Uno): base servo on pin 11, up/down servo on pin 12, hall-effect magnet sensor on A0.
- A camera pointed at the board (the Mac's built-in one works for testing).

## Files

| File | What it does |
|---|---|
| `arduino/board/board.ino` | Board Arduino. Send `0`-`8` to light a hole, `x` to turn them all off. |
| `arduino/arm/arm.ino` | Arm Arduino. `M90,45` moves the servos, `P3` goes to a preset, `R` reads the magnet sensor. |
| `arduino/led_test/`, `arduino/servo_check/` | Test sketches for checking wiring. |
| `arm.py` | Controls the arm from the computer. Has a calibrate mode for saving each hole's position. |
| `camera.py` | Cuts the camera picture into 9 zoomed-in views, one per hole. |
| `gui.py` | The screen: shows how each model sees the board, plus score and efficiency tables. |
| `game.py` | Simple on-screen version of the game that lights the matching LED. |
| `snn/` | The spiking neural network. |
| `yolo/` | The YOLO bot. |

## Setup

```bash
python3 -m venv vn
source vn/bin/activate
pip install -r requirements.txt
```

Upload `board.ino` and `arm.ino` to their Arduinos with the Arduino IDE. Close the Serial Monitor before running any Python, or the port will be busy.

If both Arduinos are plugged in at once, set `PORT` at the top of `game.py` (board) and `arm.py` (arm). `ls /dev/cu.usbmodem*` lists them.

The YOLO bot needs a Roboflow key:

```bash
export ROBOFLOW_API_KEY=your_key_here
```

## Running

```bash
python gui.py              # the main screen
python camera.py           # check the 9 hole views line up with the board
python arm.py calibrate    # save the arm position for each hole
python arm.py test         # hit every saved hole
```

## Status

Working: LEDs, servos, camera split, GUI with the SNN view.

Still to do:
- The game loop that ties the board, camera, model and arm together and fills in the score table.
- YOLO trained on photos of the board. Right now the YOLO side of the GUI is a stand-in that just picks the brightest hole.
