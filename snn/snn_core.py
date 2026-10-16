import numpy as np

GRID_W, GRID_H = 64, 48     # one neuron per grid cell
THRESHOLD = 0.5             # how much a neuron must "charge" before it spikes
DECAY = 0.8                 # leak: each step a neuron keeps 80% of its charge

v = np.zeros((GRID_H, GRID_W))   # membrane potential ("charge") of every neuron
prev = None                      # last frame, to compare against

def step(frame_gray):
    """frame_gray: 2D numpy array (H x W, 0-255). Returns (x, y) to click, or None."""
    global v, prev
    # 1. Shrink the frame to the neuron grid (average blocks of pixels).
    h, w = frame_gray.shape
    small = frame_gray[: h - h % GRID_H, : w - w % GRID_W]
    small = small.reshape(GRID_H, h // GRID_H, GRID_W, w // GRID_W).mean(axis=(1, 3))

    if prev is None:
        prev = small
        return None

    # 2. Events: how much each cell got DARKER since last frame (0 = no change, 1 = white->black).
    #    Unchanged cells give 0, so they cost (almost) nothing. That's the event-driven idea.
    events = np.clip((prev - small) / 255, 0, 1)
    prev = small

    # 3. Leaky integrate-and-fire: leak a bit, add the input, spike if over threshold.
    #    Small flickers leak away; a real dot pushes the neuron over the threshold.
    v = v * DECAY + events
    spikes = v >= THRESHOLD
    v[spikes] = 0               # reset neurons that just fired

    # 4. Read out: the dot is where the spikes are.
    if not spikes.any():
        return None
    ys, xs = np.nonzero(spikes)
    cell_w, cell_h = w / GRID_W, h / GRID_H
    return (xs.mean() + 0.5) * cell_w, (ys.mean() + 0.5) * cell_h
