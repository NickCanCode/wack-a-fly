"""Wack-a-Fly screen: the live camera as each model sees it, a SNN vs YOLO table, and a switch.

Run:  python main.py   # the game: this screen plus the board and arm
      python gui.py    # just this screen, no Arduinos needed
"""
import base64
import time
import tkinter as tk
from tkinter import ttk

import cv2
import numpy as np

import camera
import snn.snn_core as snn

MODELS = ["SNN", "YOLO"]
STATS = ["Hits", "Misses", "Hit rate", "Avg time (ms)"]
EFF = ["Work grows with", "Big O", "Looked at this frame", "Share of picture", "Time per frame (ms)"]
EFF_FIXED = {                                   # rows that never change: [SNN, YOLO]
    "Work grows with": ["how much moves", "picture size"],
    "Big O": ["O(changes)", "O(pixels)"],
}
W, H = 400, 300   # size of each picture panel
BRIGHT_GAP = 20   # YOLO stand-in: how much brighter the lit hole must be than the others (0-255)

VOCAB = (
    "Big O: how the work grows when the input gets bigger.  "
    "O(pixels) = twice the pixels, twice the work, every frame.  "
    "O(changes) = the work only grows with how much is moving; a still board costs almost nothing.\n"
    "Frame: one picture from the camera.   Pixel: one dot in that picture.   "
    "Neuron: one cell in the SNN's 64 x 48 grid; it charges up when its spot changes.\n"
    "Event (red): a spot that changed since the last frame.   "
    "Spike (white): a neuron firing because it charged up enough.\n"
    "Note: here the SNN runs on a normal laptop, so it still scans every cell to find the changes, "
    "and the time row shows that honestly. On a neuromorphic chip, cells that don't change cost nothing."
)


def make_table(root, rows):
    """A table with a row per stat and a column per model, all starting as '-'."""
    table = ttk.Treeview(root, columns=["stat"] + MODELS, show="headings", height=len(rows))
    table.heading("stat", text="")
    table.column("stat", width=170, anchor="w")
    for model in MODELS:
        table.heading(model, text=model)
        table.column(model, width=140, anchor="center")
    for stat in rows:
        table.insert("", "end", iid=stat, values=[stat, "-", "-"])
    return table


def set_cell(table, stat, model, value):
    """Change one cell of a table: the row for stat, the column for model."""
    row = list(table.item(stat, "values"))
    row[MODELS.index(model) + 1] = value
    table.item(stat, values=row)


def panel(img, title, target, grid=False):
    """Resize a picture, draw the 9 hole boxes (thick = the hole the model picked) and a title.
    grid=True: the picture is the 3x3 grid of zoomed holes, so each box is one ninth of it."""
    sx, sy = W / img.shape[1], H / img.shape[0]
    img = cv2.resize(img, (W, H), interpolation=cv2.INTER_NEAREST)
    if grid:
        boxes = [(c * W // 3, r * H // 3, (c + 1) * W // 3, (r + 1) * H // 3) for r in range(3) for c in range(3)]
    else:
        half = camera.BOX // 2
        boxes = [(int((x - half) * sx), int((y - half) * sy), int((x + half) * sx), int((y + half) * sy))
                 for x, y in camera.HOLES]
    for i, (x1, y1, x2, y2) in enumerate(boxes):
        picked = i == target
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 255) if picked else (70, 70, 70), 4 if picked else 2)
    cv2.putText(img, title, (10, 25), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 2)
    return img


def snn_guess(holes):
    """The SNN: glue the 9 holes into one 3x3 picture and look for what just got brighter.
    Returns the hole it saw light up this frame, or None."""
    gray = cv2.cvtColor(camera.grid(holes), cv2.COLOR_BGR2GRAY)  # black and white
    point = snn.step(gray, brighter=True)  # a point to hit, or None
    if point is None:
        return None
    x, y = point
    return int(y // camera.SIZE) * 3 + int(x // camera.SIZE)  # which square the point is in


def yolo_guess(holes):
    """Stand-in until YOLO is trained on the board: the brightest hole wins.
    It only answers if that hole is clearly brighter than the rest, so it can't guess a dark board."""
    brightness = [cv2.cvtColor(h, cv2.COLOR_BGR2GRAY).mean() for h in holes]
    best = int(np.argmax(brightness))
    others = (sum(brightness) - brightness[best]) / 8
    return best if brightness[best] - others > BRIGHT_GAP else None


class Dashboard:
    def __init__(self, root, cam):
        self.root, self.cam = root, cam
        self.active = "SNN"
        self.results = {m: [] for m in MODELS}
        self.snn_pick = None
        self.picks = {m: None for m in MODELS}   # the hole each model saw this frame, or None
        self.ms = {m: 0.0 for m in MODELS}   # smoothed time per frame for each model
        root.title("Wack-a-Fly")

        # Left: the mirror (picture + one line explaining it)
        left = tk.Frame(root, padx=10, pady=10)
        left.grid(row=0, column=0, sticky="n")
        self.mirror = tk.Label(left)
        self.mirror.pack()
        self.caption = tk.Label(left, wraplength=2 * W)
        self.caption.pack(pady=(10, 0))

        # Right: the results table, the efficiency table, then the switch
        right = tk.Frame(root, padx=10, pady=10)
        right.grid(row=0, column=1, sticky="n")
        tk.Label(right, text="SCORE", font=("", 14, "bold")).pack(anchor="w")
        self.table = make_table(right, STATS)
        self.table.pack(pady=(4, 12))
        tk.Label(right, text="EFFICIENCY", font=("", 14, "bold")).pack(anchor="w")
        self.eff = make_table(right, EFF)
        self.eff.pack(pady=(4, 12))
        for stat, values in EFF_FIXED.items():
            self.eff.item(stat, values=[stat] + values)

        self.switch = tk.Button(right, text="PLAYING: SNN", command=self.toggle)
        self.switch.pack(fill="x")

        # Bottom: the words, explained
        tk.Label(root, text=VOCAB, justify="left", wraplength=1150, padx=10, pady=10).grid(
            row=1, column=0, columnspan=2, sticky="w")

        self.tick()

    def toggle(self):
        self.active = "YOLO" if self.active == "SNN" else "SNN"
        self.switch.config(text=f"PLAYING: {self.active}")

    def tick(self):
        """Every frame: run BOTH models (so both efficiency columns stay live), show the active one."""
        ok, frame = self.cam.read()
        if ok:
            views = {}
            for model, run in (("SNN", self.snn_view), ("YOLO", self.yolo_view)):
                start = time.perf_counter()
                views[model] = run(frame)
                ms = (time.perf_counter() - start) * 1000
                self.ms[model] = 0.9 * self.ms[model] + 0.1 * ms   # smooth it so it's readable

            for model, (img, caption, looked, share) in views.items():
                set_cell(self.eff, "Looked at this frame", model, looked)
                set_cell(self.eff, "Share of picture", model, share)
                set_cell(self.eff, "Time per frame (ms)", model, f"{self.ms[model]:.1f}")

            img, caption, _, _ = views[self.active]
            self.caption.config(text=caption)
            self.photo = tk.PhotoImage(data=base64.b64encode(cv2.imencode(".png", img)[1].tobytes()))
            self.mirror.config(image=self.photo)
        self.show_score()
        self.root.after(30, self.tick)   # again in 30 ms

    def snn_view(self, frame):
        """Camera next to what the SNN gets: only the parts of the holes that changed since the last frame."""
        self.picks["SNN"] = snn_guess(camera.split(frame))
        if self.picks["SNN"] is not None:
            self.snn_pick = self.picks["SNN"]   # keep showing the last pick after the spikes fade

        seen = np.zeros((snn.GRID_H, snn.GRID_W, 3), np.uint8)
        seen[..., 2] = np.clip(snn.events * 4 * 255, 0, 255).astype(np.uint8)   # change = red
        seen[snn.spikes] = (255, 255, 255)                                       # spike = white

        total = snn.GRID_W * snn.GRID_H
        changed = int((snn.events > 0.02).sum())
        if changed == 0:
            caption = "Nothing changed, so the SNN sees nothing and does nothing."
        else:
            caption = f"Change! {changed} of {total} neurons got input -> picked hole {self.snn_pick}"
        img = np.hstack([panel(frame, "Camera", None), panel(seen, "SNN sees: only change", self.snn_pick, grid=True)])
        return img, caption, f"{changed:,} changed cells", f"{100 * changed / total:.1f}%"

    def yolo_view(self, frame):
        """Camera next to what a frame-based model gets: the whole picture, every frame."""
        pick = self.picks["YOLO"] = yolo_guess(camera.split(frame))
        h, w = frame.shape[:2]
        caption = f"Checks all {w * h:,} pixels every frame, changed or not -> picked hole {pick}"
        img = np.hstack([panel(frame, "Camera", None), panel(frame, "YOLO sees: everything", pick)])
        return img, caption, f"{w * h:,} pixels", "100%"

    def record(self, model, hit, ms):
        """Add one real result. The game calls this from its own thread, so it only saves the result;
        tick() draws the table, because only the window's own thread may change the window."""
        self.results[model].append((hit, ms))

    def show_score(self):
        """Fill the SCORE table from the results so far."""
        for model, res in self.results.items():
            if not res:
                continue
            hit_ms = [t for h, t in res if h]   # average only the hits: a miss just waited out the timeout
            hits = len(hit_ms)
            set_cell(self.table, "Hits", model, hits)
            set_cell(self.table, "Misses", model, len(res) - hits)
            set_cell(self.table, "Hit rate", model, f"{100 * hits / len(res):.0f}%")
            set_cell(self.table, "Avg time (ms)", model, f"{sum(hit_ms) / hits:.0f}" if hits else "-")


if __name__ == "__main__":
    cam = cv2.VideoCapture(camera.CAMERA)
    root = tk.Tk()
    gui = Dashboard(root, cam)
    root.mainloop()
    cam.release()
