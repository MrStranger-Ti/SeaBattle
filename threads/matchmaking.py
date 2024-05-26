import threading
import time

from main import create_session

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
        self.total_players = 1

    def run(self):
        while self.run_cycle:
            time.sleep(3)
            if len(PLAYERS_QUEUE) >= self.total_players:
                create_session(PLAYERS_QUEUE[:self.total_players])
                PLAYERS_IN_GAME.extend(PLAYERS_QUEUE[:self.total_players])
                del PLAYERS_QUEUE[:self.total_players]


def start_matchmaking() -> threading.Thread:
    """
    Запуск потока для подбора игроков.
    """

    thread = Matchmaking()
    thread.start()
    return thread
