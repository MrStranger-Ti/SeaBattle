import random
import threading
import time
from datetime import datetime, timedelta

import telebot

from objects.exeptions import PositionError, CellOpenedError
from objects.player import Player
from states.states import get_or_add_state


class Session(threading.Thread):
    """
    Сессия игры.

    При каждом запуске игры создается сессия, в которой идет игра до какого-то результата.

    Attributes:
        is_running (bool): выполнять ли поток (сессию)
        bot (telebot.TeleBot): основной объект бота из библиотеки telebot
        players (list[Player]): список из игроков
        leading (Player): ведущий игрок
    """
    def __init__(self, bot: telebot.TeleBot, players: list[telebot.types.User]):
        super().__init__()
        self.is_running: bool = True
        self.bot: telebot.TeleBot = bot
        self.players: list[Player] = [Player(user) for user in players]
        self.leading: Player | None = None

    def run(self) -> None:
        # подготовка к игре
        ...

        # запуск игры
        self.start_game()

        # контроль игры
        while self.is_running:
            time.sleep(1)
            self.update()

    def start_game(self) -> None:
        """
        Запуск игры.
        """
        # Всем игрокам в сессии выставляем состояние waiting_for_move и уведомляем о начале игры.
        for player in self.players:
            player.opponent = self.get_opponent(player)
            player_state = get_or_add_state(player.object.id)
            player_state.name = 'waiting_for_move'
            self.bot.send_message(player.object.id, 'Игра начинается.')

        # Случайным образом определяем ведущего игрока.
        # Выставляем ему состояние making_move и просим сделать ход.
        self.leading = random.choice(self.players)
        leading_player_state = get_or_add_state(self.leading.object.id)
        leading_player_state.name = 'making_move'
        self.ask_for_a_position()

    def update(self) -> None:
        """
        Обновление сессии.

        Здесь происходит проверка состояний всех игроков.
        Состояния ведущего игрока проверяются отдельно.
        """
        for player in self.players:
            player_state = get_or_add_state(player.object.id)

            # Если игрок хочет покинуть игру, то удаляем его из сессии.
            if player_state.name == 'leaving_game':
                self.remove_player(player)

        # Получаем состояние ведущего игрока
        leading_player_state = get_or_add_state(self.leading.object.id)

        # Если у ведущего игрока состояние check_move, то пробуем раскрыть клетку у соперника.
        if leading_player_state.name == 'check_move':

            try:
                # Пробуем открыть клетку соперника. Если мы успешно ее открыли, то узнаем корабль это или нет.
                is_ship = player.open_opponent_cell(leading_player_state.message.text)
            except (PositionError, CellOpenedError) as exc:

                # Так как произошла ошибка, то меняем состояние на making_move,
                # чтобы игрок смог попробовать еще раз сделать ход.
                leading_player_state.name = 'making_move'

                # Если клетки, который ввел пользователь, не существует,
                # то отправляем ему соответствующее сообщение.
                if isinstance(exc, PositionError):
                    self.send_message(self.leading, 'Неверная клетка.')

                # Если клетка, который ввел пользователь, уже открыта,
                # то отправляем ему соответствующее сообщение.
                if isinstance(exc, CellOpenedError):
                    self.send_message(self.leading, 'Эта клетка уже открыта.')

                return

            # Отправляем пользователю сообщение, попал он или нет.
            if is_ship:
                self.bot.send_message(self.leading.object.id, 'Вы попали.')
            else:
                self.bot.send_message(self.leading.object.id, 'Вы не попали.')

            # Изменяем ведущего игрока.
            self.change_leading()

    def get_opponent(self, player: Player) -> Player:
        """
        Получение следующего игрока в списке.
        """
        if player == self.players[-1]:
            return self.players[0]

        ind = self.players.index(player)
        return self.players.index(ind + 1)

    def send_message(self, player: Player, message: str) -> None:
        """
        Отправка сообщения игроку.
        """
        self.bot.send_message(player.object.id, message)

    def ask_for_a_position(self) -> None:
        """
        Отправка игроку сообщения о предложении выбрать клетку.
        """
        self.send_message(self.leading, 'Выберите клетку.')

    def change_leading(self) -> None:
        """
        Изменение ведущего игрока.

        Следующим ведущим игроком должен стать соперник текущего ведущего игрока.
        """
        # У старого ведущего игрока изменяем состояние на waiting_move
        old_leading_player_state = get_or_add_state(self.leading.object.id)
        old_leading_player_state.name = 'waiting_move'

        # Изменяем ведущего игрока
        self.leading = self.leading.opponent

        # У нового ведущего игрока изменяем состояние на making_move
        new_leading_player_state = get_or_add_state(self.leading.object.id)
        new_leading_player_state.name = 'making_move'
        self.ask_for_a_position()

    def remove_player(self, player: Player) -> None:
        """
        Удаление игрока из сессии.
        """
        # После удаления выставляем состояние пользователя на main и меняем флаг in_game на False
        self.players.remove(player)
        state = get_or_add_state(player.object.id)
        state.name = 'main'
        state.in_game = False

        # Если игроков в сессии меньше 2, то заканчиваем игру и подводим итоги
        if len(self.players) < 2:
            self.finish_game()

    def finish_game(self) -> None:
        """
        Подводим итоги игры.

        Единственному оставшемуся игроку в сессии отправляем поздравление,
        изменяем его состояние и завершаем сессию.
        """
        if self.players:
            winner = self.players[0]
            winner_state = get_or_add_state(winner.object.id)
            winner_state.name = 'main'

            self.bot.send_message(winner.object.id, 'Поздравляем, вы выиграли!')

        self.stop_session()

    def stop_session(self) -> None:
        """
        Завершение сессии.

        Завершаем цикл, изменив self.is_running на False.
        """
        self.is_running = False
