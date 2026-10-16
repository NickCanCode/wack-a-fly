import time
import numpy as np
import pyautogui
import snn.snn_core as snn_core                      # brain file

scale = pyautogui.screenshot().width / pyautogui.size().width   # same as YOLO

print("Starting in 3 seconds...")
time.sleep(3)

while True:
    frame = np.array(pyautogui.screenshot().convert("L"))   # "L" = black and white
    h, w = frame.shape
    frame = frame[:, :w // 2]                                # left half, same as YOLO

    target = snn_core.step(frame)     # brain: "click here" or None
    if target is not None:
        x, y = target
        pyautogui.click(x / scale, y / scale)
        print("clicked", int(x / scale), int(y / scale))