import random
import select
import sys
import time

initBoard = {
    row: {'1': False, '2': False, '3': False}
    for row in ('a', 'b', 'c')
}
gameLength = 30  # Set the game length in seconds


def start_game():
    liveBoard = {row: cells.copy() for row, cells in initBoard.items()}
    pts = 0
    deadline = time.monotonic() + gameLength
    print("Board initialized")
    print(liveBoard)
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break

        print("Enter your guess (e.g., a1, b2, c3): ", end="", flush=True)
        if not select.select([sys.stdin], [], [], remaining)[0]:
            break

        try:
            uGuess = input().strip().lower()
        except EOFError:
            break

        if len(uGuess) != 2 or uGuess[0] not in liveBoard or uGuess[1] not in liveBoard['a']:
            print("Invalid guess. Enter a row and column, such as a1.")
            continue

        x, y = uGuess
        random_x = random.choice(('a', 'b', 'c'))
        random_y = str(random.randint(1, 3))

        if uGuess == random_x + random_y and not liveBoard[x][y]:
            liveBoard[x][y] = True
            pts += 1
            print(f"Hit at {uGuess}!")
            print("Current Board State:")
            print(liveBoard)
        elif uGuess == random_x + random_y:
            print(f"You already hit {uGuess}.")
        else:
            print(f"Miss at {uGuess}.")

    print("Time's up!")
    print(f"Final score: {pts}")

start_game()
