import random
import time
import tkinter as tk
import serial
import serial.tools.list_ports

PORT = "auto"   # "auto" finds the Arduino, or a path like "/dev/cu.usbmodem31101", or None for no Arduino
ROUNDS = 20

if PORT == "auto":
    found = [p.device for p in serial.tools.list_ports.comports()
             if "usbmodem" in p.device or "usbserial" in p.device]
    if not found:
        raise SystemExit("No Arduino found. Plug it in (ls /dev/cu.*) or set PORT = None.")
    PORT = found[0]
    print(f"Using {PORT}")

arduino = None
if PORT:
    arduino = serial.Serial(PORT, 9600)
    time.sleep(2)   # Arduino restarts when connected, wait for it


def send(message):
    if arduino:
        arduino.write(message.encode())


# Window with a 3x3 grid of holes
root = tk.Tk()
canvas = tk.Canvas(root, width=600, height=600, bg="white")
canvas.pack()

holes = []
for row in range(3):
    for col in range(3):
        x = 100 + col * 200
        y = 100 + row * 200
        holes.append(canvas.create_oval(x - 60, y - 60, x + 60, y + 60, fill="lightgray"))

lit = None      # number of the lit hole (0-8)
start = 0       # when it lit up
times = []


def light_hole():
    global lit, start
    lit = random.randint(0, 8)
    canvas.itemconfig(holes[lit], fill="red")
    send(str(lit))
    start = time.time()


def on_click(event):
    global lit
    clicked = canvas.find_overlapping(event.x, event.y, event.x, event.y)
    if lit is None or holes[lit] not in clicked:
        return

    times.append(time.time() - start)
    print(f"Round {len(times)}: {times[-1] * 1000:.0f} ms")

    canvas.itemconfig(holes[lit], fill="lightgray")
    send("x")
    lit = None

    if len(times) < ROUNDS:
        root.after(random.randint(500, 2000), light_hole)
    else:
        print(f"Average: {sum(times) / len(times) * 1000:.0f} ms")


canvas.bind("<Button-1>", on_click)
root.after(1000, light_hole)
root.mainloop()
