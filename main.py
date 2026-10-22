"""Wack-a-Fly: the whole game in one window.

The window (gui.py) shows the camera and runs both models on every frame. The game loop below runs
next to it on its own thread: light a random hole, wait for the model on the switch to guess,
hit that hole with the arm, add the result to the SCORE table, repeat.

    python main.py   # close the window to stop
"""
import random
import threading
import time
import tkinter as tk

import cv2

import arm
import board
import camera
from gui import Dashboard

TIMEOUT = 3      # seconds to wait for a guess before it counts as a miss
PAUSE = 1        # seconds of dark board between rounds
USE_ARM = True   # False = just guess, don't move the arm (no arm Arduino needed)


def game():
    """The game loop. It has its own thread so the window keeps updating while the game waits."""
    rounds = 0
    while True:
        time.sleep(PAUSE)  # keep the board dark for a moment, so the SNN sees the LED turn on

        rounds += 1
        model = gui.active  # whichever model the switch is on
        hole = random.randint(0, 8)  # Randomly select a hole
        print(f"Round {rounds} ({model}): lit hole {hole}")
        board.light(board_conn, hole)  # Send the selected hole to the game board

        # Wait until the model guesses a hole (give up after TIMEOUT seconds).
        # The window runs the models on every frame and puts their guesses in gui.picks.
        guess = None
        start = time.time()
        while guess is None and time.time() - start < TIMEOUT:
            time.sleep(0.01)
            guess = gui.picks[model]
        seconds = time.time() - start

        hit = guess == hole
        gui.record(model, hit, seconds * 1000)
        if guess is None:
            print(f"  {model} didn't see anything: MISS")
        else:
            print(f"  {model} guessed {guess}: {'HIT' if hit else 'MISS'} ({seconds * 1000:.0f} ms)")

        # The arm hits wherever the model said, right or wrong
        if USE_ARM and guess is not None:
            found = arm.hit(arm_conn, guess)
            print(f"  arm hit hole {guess}: {'magnet' if found else 'no magnet'}")

        board.off(board_conn)


board_conn = board.connect()  # Connect to the game board
arm_conn = arm.connect() if USE_ARM else None  # Connect to the arm
cam = cv2.VideoCapture(camera.CAMERA)  # Turn on the camera

root = tk.Tk()
gui = Dashboard(root, cam)
threading.Thread(target=game, daemon=True).start()  # start the game next to the window
root.mainloop()  # the window runs here until you close it

board.off(board_conn)
cam.release()
