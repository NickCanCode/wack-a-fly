"""Wack-a-Fly screen: the live camera as each model sees it, a SNN vs YOLO table, and a switch.

Run:  python gui.py
Later, the game loop adds real results with:  gui.record("SNN", hit=True, ms=240)
"""
import base64
import time
import tkinter as tk
import tkinter.font as tkfont
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

# Minecraft look
DIRT, GRASS = "#79553A", "#5D9B32"
STONE, STONE_DARK, STONE_LIGHT = "#8B8B8B", "#373737", "#C6C6C6"
BUTTON, BUTTON_HOVER = "#6F6F6F", "#7D88C2"
GOLD = "#FFFF55"   # Minecraft's yellow text

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


def pick_font():
    """Use a pixel font if one is installed, otherwise a blocky monospace one."""
    installed = tkfont.families()
    for name in ("Minecraft", "Minecraftia", "Press Start 2P", "VT323", "Monaco", "Courier New"):
        if name in installed:
            return name
    return "Courier"


def style_tables(font):
    style = ttk.Style()
    style.theme_use("clam")   # the Mac default theme ignores colours
    style.configure("Treeview", background=STONE, fieldbackground=STONE, foreground="white",
                    font=(font, 12), rowheight=28, borderwidth=0)
    style.configure("Treeview.Heading", background=STONE_DARK, foreground=GOLD,
                    font=(font, 12, "bold"), relief="flat")
    style.map("Treeview", background=[("selected", GRASS)])
    style.map("Treeview.Heading", background=[("active", STONE_DARK)])


def slot(parent):
    """A stone panel with a dark border, like a Minecraft inventory slot."""
    return tk.Frame(parent, bg=STONE, highlightbackground=STONE_DARK, highlightthickness=4,
                    padx=10, pady=10)


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


def panel(img, title, target):
    """Resize a picture, draw the 9 hole boxes (thick = the hole the model picked) and a title."""
    sx, sy = W / img.shape[1], H / img.shape[0]
    img = cv2.resize(img, (W, H), interpolation=cv2.INTER_NEAREST)
    half = camera.BOX // 2
    for i, (x, y) in enumerate(camera.HOLES):
        picked = i == target
        cv2.rectangle(img, (int((x - half) * sx), int((y - half) * sy)),
                      (int((x + half) * sx), int((y + half) * sy)),
                      (85, 255, 255) if picked else (70, 70, 70), 4 if picked else 2)
    # Minecraft-style text: dark shadow first, white on top
    cv2.putText(img, title, (12, 27), cv2.FONT_HERSHEY_DUPLEX, 0.7, (63, 63, 63), 2)
    cv2.putText(img, title, (10, 25), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 2)
    return cv2.copyMakeBorder(img, 4, 4, 4, 4, cv2.BORDER_CONSTANT, value=(55, 55, 55))


def which_hole(x, y):
    """Camera point -> the hole it's inside, or None."""
    for i, (hx, hy) in enumerate(camera.HOLES):
        if abs(x - hx) <= camera.BOX // 2 and abs(y - hy) <= camera.BOX // 2:
            return i
    return None


class Dashboard:
    def __init__(self, root, cam):
        self.root, self.cam = root, cam
        self.active = "SNN"
        self.results = {m: [] for m in MODELS}
        self.snn_pick = None
        self.ms = {m: 0.0 for m in MODELS}   # smoothed time per frame for each model
        root.title("Wack-a-Fly")
        root.configure(bg=DIRT)
        font = pick_font()
        style_tables(font)

        # Top: grass title bar
        tk.Label(root, text="WACK-A-FLY", bg=GRASS, fg=GOLD, font=(font, 26, "bold"), pady=8).grid(
            row=0, column=0, columnspan=2, sticky="ew")

        # Left: the mirror (picture + one line explaining it)
        left = slot(root)
        left.grid(row=1, column=0, padx=12, pady=12, sticky="n")
        self.mirror = tk.Label(left, bg=STONE)
        self.mirror.pack()
        self.caption = tk.Label(left, bg=STONE, fg="white", font=(font, 14), wraplength=2 * W)
        self.caption.pack(pady=(10, 0))

        # Right: the results table, the efficiency table, then the switch
        right = slot(root)
        right.grid(row=1, column=1, padx=12, pady=12, sticky="n")
        tk.Label(right, text="SCORE", bg=STONE, fg=GOLD, font=(font, 14, "bold")).pack(anchor="w")
        self.table = make_table(right, STATS)
        self.table.pack(pady=(4, 12))
        tk.Label(right, text="EFFICIENCY", bg=STONE, fg=GOLD, font=(font, 14, "bold")).pack(anchor="w")
        self.eff = make_table(right, EFF)
        self.eff.pack(pady=(4, 12))
        for stat, values in EFF_FIXED.items():
            self.eff.item(stat, values=[stat] + values)

        # The switch: a chunky stone button (a Label, because Mac buttons ignore colours)
        self.switch = tk.Label(right, text="PLAYING: SNN", bg=BUTTON, fg="white", font=(font, 14, "bold"),
                               relief="raised", bd=4, padx=16, pady=8, cursor="hand2")
        self.switch.pack(fill="x")
        self.switch.bind("<Button-1>", lambda e: self.toggle())
        self.switch.bind("<Enter>", lambda e: self.switch.config(bg=BUTTON_HOVER))
        self.switch.bind("<Leave>", lambda e: self.switch.config(bg=BUTTON))

        # Bottom: the words, explained
        tk.Label(root, text=VOCAB, justify="left", wraplength=1150, bg=STONE_DARK, fg=STONE_LIGHT,
                 font=(font, 11), padx=12, pady=10).grid(
            row=2, column=0, columnspan=2, padx=12, pady=(0, 12), sticky="ew")

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
                self.set_eff(model, f"{looked}", share, f"{self.ms[model]:.1f}")

            img, caption, _, _ = views[self.active]
            self.caption.config(text=caption)
            self.photo = tk.PhotoImage(data=base64.b64encode(cv2.imencode(".png", img)[1].tobytes()))
            self.mirror.config(image=self.photo)
        self.root.after(30, self.tick)   # again in 30 ms

    def set_eff(self, model, looked, share, ms):
        col = MODELS.index(model) + 1
        for stat, value in (("Looked at this frame", looked), ("Share of picture", share),
                            ("Time per frame (ms)", ms)):
            row = list(self.eff.item(stat, "values"))
            row[col] = value
            self.eff.item(stat, values=row)

    def snn_view(self, frame):
        """Camera next to what the SNN gets: only the parts that changed since the last frame."""
        point = snn.step(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), brighter=True)
        if point is not None:
            self.snn_pick = which_hole(*point)

        seen = np.zeros((snn.GRID_H, snn.GRID_W, 3), np.uint8)
        seen[..., 2] = np.clip(snn.events * 4 * 255, 0, 255).astype(np.uint8)   # change = red
        seen[snn.spikes] = (255, 255, 255)                                       # spike = white

        total = snn.GRID_W * snn.GRID_H
        changed = int((snn.events > 0.02).sum())
        if changed == 0:
            caption = "Nothing changed, so the SNN sees nothing and does nothing."
        else:
            caption = f"Change! {changed} of {total} neurons got input -> picked hole {self.snn_pick}"
        img = np.hstack([panel(frame, "Camera", None), panel(seen, "SNN sees: only change", self.snn_pick)])
        return img, caption, f"{changed:,} changed cells", f"{100 * changed / total:.1f}%"

    def yolo_view(self, frame):
        """Camera next to what a frame-based model gets: the whole picture, every frame."""
        # Stand-in until YOLO is trained on the board: the brightest hole wins.
        pick = int(np.argmax([cv2.cvtColor(c, cv2.COLOR_BGR2GRAY).mean() for c in camera.split(frame)]))
        h, w = frame.shape[:2]
        caption = f"Checks all {w * h:,} pixels every frame, changed or not -> picked hole {pick}"
        img = np.hstack([panel(frame, "Camera", None), panel(frame, "YOLO sees: everything", pick)])
        return img, caption, f"{w * h:,} pixels", "100%"

    def record(self, model, hit, ms):
        """Add one real result to the table."""
        self.results[model].append((hit, ms))
        res = self.results[model]
        hits = sum(h for h, _ in res)
        values = [hits, len(res) - hits, f"{100 * hits / len(res):.0f}%", f"{sum(t for _, t in res) / len(res):.0f}"]
        col = MODELS.index(model) + 1
        for stat, value in zip(STATS, values):
            row = list(self.table.item(stat, "values"))
            row[col] = value
            self.table.item(stat, values=row)


if __name__ == "__main__":
    cam = cv2.VideoCapture(camera.CAMERA)
    root = tk.Tk()
    gui = Dashboard(root, cam)
    root.mainloop()
    cam.release()
