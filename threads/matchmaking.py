import threading
import time

from main import start_game

PLAYERS_IN_GAME = []
PLAYERS_QUEUE = []


class Matchmaking(threading.Thread):
    """
    Поток для подбора игроков.

    Для завершения потока необходимо изменить self.run_cycle на False.
    """

    def __init__(self):
        super().__init__()
        self.run_cycle = True

    def run(self):
        while self.run_cycle:
            time.sleep(3)
            if len(PLAYERS_QUEUE) >= 4:
                start_game(PLAYERS_QUEUE[:4])
                PLAYERS_IN_GAME.extend(PLAYERS_QUEUE[:4])
                del PLAYERS_QUEUE[:4]


def start_matchmaking() -> threading.Thread:
    """
    Запуск потока для подбора игроков.
    """

    thread = Matchmaking()
    thread.start()
    return thread
