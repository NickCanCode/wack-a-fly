# Wack-a-Fly

A whack-a-mole board where a robot arm does the whacking. A camera watches the board, and one of two models decides which hole to hit. The point of the project is to show how differently the two models "see" the same thing:

- **SNN** (spiking neural network): works more like a brain. It only reacts to what changes.
- **YOLO**: a normal object detector. It looks at the whole picture, every frame.

Neuromorphic Computing class project.

## Two ways to see the board

Imagine you're watching the board and nothing is happening. All 9 LEDs are off. Then one turns on.

**YOLO** looks at every single frame from scratch, whether anything happened or not. With a 640 x 480 camera that's 307,200 pixels, run through the whole network, about 30 times a second. A still, boring board costs exactly as much as a busy one.

**The SNN** is closer to how your eyes work. Your eyes don't re-read the whole room every moment; you notice when something moves or flashes. The SNN only gets input where the picture changed since the last frame. A still board gives it nothing to do.

## How YOLO works

1. Take a frame from the camera.
2. Resize it and feed every pixel into a convolutional neural network (CNN).
3. The network outputs boxes around things it recognises, each with a confidence score.
4. Pick the most confident box. Its centre is where to hit.
5. Next frame, start over. Nothing is remembered between frames.

YOLO runs on a normal computer, which keeps memory and processing separate (the "von Neumann" design). For every layer of the network, the weights have to be moved from memory to the processor and back. That shuttling is a big part of why this kind of model uses so much power.

## How the SNN works

This is what `snn/snn_core.py` does, step by step.

**1. Shrink the picture into a grid of neurons.**
The camera frame is turned grey and averaged down to a 64 x 48 grid. Each cell is one neuron, so there are 3,072 neurons watching the board.

**2. Only pass on what changed.**
Each neuron compares its cell to the last frame: "how much brighter did my spot just get?" If nothing changed, its input is 0. This input is called an **event**.

**3. Charge up, and leak.**
Every neuron has a charge (the "membrane potential"). Each frame:

```
charge = charge x 0.8 + event
```

The `x 0.8` is the leak: a neuron slowly forgets old input. The `+ event` adds anything new.

**4. Spike when the charge gets high enough.**
If the charge reaches 0.5, the neuron **spikes** (fires) and its charge resets to 0. This is why it's called a *leaky integrate-and-fire* neuron: it leaks, integrates (adds up) input, and fires.

**5. Read the answer from the spikes.**
The hole to hit is wherever the spiking neurons are.

### Why the leak matters

The leak is what lets the SNN tell a real flash from noise:

| What happens in a cell | Charge over a few frames | Spikes? |
|---|---|---|
| LED turns on (big jump, event = 0.8) | 0.8 | Yes, right away |
| Medium change twice in a row (event = 0.3) | 0.3, then 0.54 | Yes, on the 2nd frame |
| Small flicker every frame (event = 0.05) | 0.05, 0.09, 0.12 ... never above 0.25 | Never |
| LED stays on (no change, event = 0) | drains back to 0 | No |

That last row surprises people: once the LED has been on for a moment, the SNN stops "seeing" it. It noticed the moment it turned on, and that's all it needs.

## Side by side

| | SNN | YOLO |
|---|---|---|
| Looks at | Only what changed | Every pixel, every frame |
| Remembers between frames | Yes (each neuron's charge) | No |
| Work grows with | How much is moving | How big the picture is |
| Big O | O(changes) | O(pixels) |
| Good at | Fast reactions, ignoring a still scene | Recognising what something is, even if it's not moving |
| Bad at | Things that don't move or change | Wasting effort on frames where nothing happened |

## What you see in the GUI

Run `python gui.py` and use the switch to flip between the two.

- **SNN view:** the camera on the left, and on the right a black grid of neurons. **Red** is an event (that spot changed). **White** is a spike. When an LED turns on you'll see a flash of red and white, then it fades back to black even though the LED is still lit.
- **YOLO view:** the camera next to the full picture, because that's what YOLO takes in every frame.
- **Efficiency table:** how much of the picture each model looked at this frame, and how long it took.

One honest note: our SNN is *simulated* on a normal laptop, so the laptop still has to scan every cell to find the changes, and the timing in the table reflects that. The real savings show up on neuromorphic chips like Intel's Loihi, where neurons that get no events use almost no power, and with event cameras that only send the pixels that changed in the first place.

## Words

- **Frame:** one picture from the camera.
- **Pixel:** one dot in that picture.
- **Neuron:** one cell in the SNN's 64 x 48 grid.
- **Event:** a spot that changed since the last frame.
- **Charge / membrane potential:** how "excited" a neuron is right now.
- **Leak:** the charge fading a little every frame (here, to 80%).
- **Threshold:** the charge needed to fire (here, 0.5).
- **Spike:** a neuron firing. It then resets to 0.
- **Big O:** how the amount of work grows as the input grows.
- **Von Neumann architecture:** the normal computer design, with memory and processor separate.
- **Neuromorphic:** hardware or models built to work like neurons, where computation happens only when there are spikes.

---

## Running the project

### Hardware

- **Board Arduino** (Uno): 9 LEDs on pins 2-10, one per hole.
- **Arm Arduino** (Uno): base servo on pin 11, up/down servo on pin 12, hall-effect magnet sensor on A0.
- A camera pointed at the board.

### Setup

```bash
python3 -m venv vn
source vn/bin/activate
pip install -r requirements.txt
```

Upload `arduino/board/board.ino` and `arduino/arm/arm.ino` to their Arduinos with the Arduino IDE. Close the Serial Monitor before running any Python, or the port will be busy. If both Arduinos are plugged in, set `PORT` at the top of `board.py` (board) and `arm.py` (arm); `ls /dev/cu.usbmodem*` lists them.

The YOLO bot needs a Roboflow key: `export ROBOFLOW_API_KEY=your_key_here`

### Commands

```bash
python gui.py              # the main screen
python camera.py           # check the 9 hole views line up with the board
python arm.py 4           # hit hole 4
python arm.py             # hit every hole, 0 to 8
```

### Files

| File | What it does |
|---|---|
| `snn/snn_core.py` | The spiking neural network (the steps above) |
| `yolo/yolo_bot.py` | The YOLO bot |
| `gui.py` | The screen showing how each model sees the board |
| `camera.py` | Cuts the camera picture into 9 views, one per hole |
| `arm.py` | Moves the arm to a hole, taps it, checks the magnet sensor. Hole angles are in the `HOLES` list. |
| `board.py` | Lights the board's LEDs. `python board.py` lights each hole in turn. |
| `arduino/board/`, `arduino/arm/` | The two Arduino sketches |
| `arduino/led_test/`, `arduino/servo_check/` | Wiring test sketches |

### Status

Working: LEDs, servos, camera split, GUI with the SNN view.

Still to do: the game loop that ties the board, camera, models and arm together and fills in the score table, and a YOLO model trained on photos of the board. Right now the YOLO side of the GUI is a stand-in that picks the brightest hole.
