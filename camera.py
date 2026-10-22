import cv2
import numpy as np

CAMERA = 0  # 0 = Mac's built-in camera; try 1 or 2 for a USB camera or iPhone
BOX = 80     # size of the square cut out around each hole
SIZE = 192   # each cut-out square is zoomed up to SIZE x SIZE

# Where each hole is in the camera picture (x, y). Hole 0 first, hole 8 last.
# Change these to match your board.
HOLES = [
    (110, 120), (320, 120), (530, 120),
    (110, 240), (320, 240), (530, 240),
    (110, 360), (320, 360), (530, 360),
]


def split(frame):
    """Cut out a square around each hole and zoom it up. Returns 9 small frames."""
    holes = []
    for x, y in HOLES:
        crop = frame[y - BOX // 2 : y + BOX // 2, x - BOX // 2 : x + BOX // 2]
        holes.append(cv2.resize(crop, (SIZE, SIZE)))
    return holes


def grid(holes):
    """Glue the 9 hole squares into one 3x3 picture, laid out like the board."""
    return np.vstack([np.hstack(holes[0:3]), np.hstack(holes[3:6]), np.hstack(holes[6:9])])


if __name__ == "__main__":
    cam = cv2.VideoCapture(CAMERA)
    while True:
        ok, frame = cam.read()
        if not ok:
            print("No picture from camera", CAMERA, "- try a different CAMERA number at the top")
            break
        holes = split(frame)

        # show all 9 hole frames in a 3x3 grid, in black and white
        #makes it gray
        gray = cv2.cvtColor(grid(holes), cv2.COLOR_BGR2GRAY)
        #makes it blurry and then makes it black and white
        gray = cv2.GaussianBlur(gray, (11, 11), 0)
        #makes only the bright part stay (light thresholding)
        _, gray = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)

        #showing camera and holes in a window
        cv2.imshow("camera", frame)
        cv2.imshow("holes", gray)

        # the brightest hole is the one with the LED on
        brightness = [cv2.cvtColor(h, cv2.COLOR_BGR2GRAY).mean() for h in holes]
        print("lit hole:", brightness.index(max(brightness)))

        if cv2.waitKey(1) == ord("q"):
            break
