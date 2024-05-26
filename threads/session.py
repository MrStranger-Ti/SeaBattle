import random
import threading
import time
from datetime import datetime, timedelta

import telebot

from objects.exeptions import PositionError
from objects.player import Player
from states.states import add_or_update_state, STATES


class Session(threading.Thread):
    """
    Сессия игры.

    При каждом запуске игры создается сессия, в которой идет игра до какого-то результата.
    """

    def __init__(self, bot: telebot.TeleBot, players: list[telebot.types.User]):
        super().__init__()
        self.bot: telebot.TeleBot = bot
        self.players: list[Player] = [Player(user) for user in players]
        for player in self.players:
            player.opponent = self.get_opponent(player)

        self.finished: bool = False
        self.is_running: bool = True
        self.leading: Player | None = None

    def run(self) -> None:
        # подготовка к игре
        ...

        # запуск игры
        self.start_game()

        # контроль игры
        while self.is_running:
            self.update()

    def start_game(self) -> None:
        for player in self.players:
            add_or_update_state(player.object.id, 'waiting_for_move')
            self.bot.send_message(player.object.id, 'Игра начинается.')

        self.leading = random.choice(self.players)
        add_or_update_state(self.leading.object.id, 'making_move')
        self.send_message(self.leading, 'Выберите клетку.')

    def update(self) -> None:
        """
        Обновление сессии.

        Если игрок проиграл, то меняем соперника игроку, который выиграл.
        Если игрок долго не отвечает, то пропускаем его ход.
        Если в игре остался один игрок, то он становится победителем и сессия заканчивается.
        """

        for player in self.players:

            if player.lost:
                self.change_opponent(player)

            # if datetime.now() - player.last_move_at > timedelta(minutes=1):
            #     self.skip_move(player)

            # if len(self.players) < 2:
            #     self.finish_game()

        leading_id = self.leading.object.id
        time.sleep(1)

        if STATES.get(leading_id).name == 'check_move':
            state = STATES.get(leading_id)

            try:
                is_ship = player.open_opponent_cell(state.message.text)
            except PositionError:
                STATES.get(leading_id).name = 'making_move'
                self.send_message(self.leading, 'Неверная клетка.')
                return

            if is_ship:
                self.bot.send_message(leading_id, 'Вы попали.')
                self.change_leading()
            else:
                self.bot.send_message(leading_id, 'Вы не попали.')

            add_or_update_state(leading_id, 'waiting_move')
            self.leading = self.leading.opponent

    def send_message(self, player: Player, message: str) -> None:
        self.bot.send_message(player.object.id, message)

    def get_opponent(self, player: Player) -> Player:
        if player == self.players[-1]:
            return self.players[0]

        ind = self.players.index(player)
        return self.players.index(ind + 1)

    def change_leading(self) -> None:
        self.leading = self.leading.opponent

    def remove_player(self, player: Player) -> None:
        self.players.remove(player)

    def change_opponent(self, loser):
        pass

    def skip_move(self, player):
        pass

    def finish_game(self) -> None:
        winner = self.players[0]
        self.bot.send_message(winner.object.id, 'Поздравляем, вы выиграли!')

        self.stop_session()

    def stop_session(self) -> None:
        self.is_running = False
