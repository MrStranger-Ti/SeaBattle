import random
import threading
import time
from datetime import datetime, timedelta

import telebot

from objects.exceptions import PositionError, CellOpenedError
from objects.player import Player
from states.states import get_or_add_state

ships = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]


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

    def prepare(self):
        """
        Подготовка к игре.
        """
        for player in self.players:
            player_state = get_or_add_state(player.object.id)
            player_state.name = 'setting_ship_position_4'
            self.bot.send_message(player.object.id, 'Установка корабля с 4-мя клетками.')
            self.bot.send_message(player.object.id, 'Выберите клетку.')

        while not self.is_everyone_ready():
            time.sleep(1)

            for player in self.players:
                player_state = get_or_add_state(player.object.id)

                if player_state.name == 'check_ship_position_4':
                    position = player_state.message.text
                    try:
                        cell = player.get_cell(position)
                    except PositionError:
                        self.bot.send_message(player.object.id, 'Неверная клетка')
                        continue

                    if player.validate_position(cell):
                        player_state.name = 'setting_ship_direction_4'

                    player.ships[4] = player.ships.get(4, 0) + 1

        # Всем игрокам в сессии выставляем состояние waiting_for_move.
        for player in self.players:
            player.opponent = self.get_opponent(player)
            player_state = get_or_add_state(player.object.id)
            player_state.name = 'waiting_for_move'

        # Случайным образом определяем ведущего игрока.
        self.leading = random.choice(self.players)

    def is_everyone_ready(self) -> bool:
        """
        Проверка игроков на готовность.

        Если все готовы, то запускаем игру.
        """
        return all(player.ready for player in self.players)

    def start_game(self) -> None:
        """
        Запуск игры.
        """
        for player in self.players:
            self.bot.send_message(player.object.id, 'Игра начинается.')

        # Выставляем ведущему игроку состояние making_move и просим сделать ход.
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
                is_ship = self.leading.open_opponent_cell(leading_player_state.message.text)
            except (PositionError, CellOpenedError) as exc:

                # Так как произошла ошибка, то меняем состояние на making_move,
                # чтобы игрок смог попробовать еще раз сделать ход.
                leading_player_state.name = 'making_move'

                # Если клетки, который ввел пользователь, не существует,
                # то отправляем ему соответствующее сообщение.
                if isinstance(exc, PositionError):
                    self.bot.send_message(self.leading, 'Неверная клетка.')

                # Если клетка, который ввел пользователь, уже открыта,
                # то отправляем ему соответствующее сообщение.
                if isinstance(exc, CellOpenedError):
                    self.bot.send_message(self.leading, 'Эта клетка уже открыта.')

                return

            # Отправляем пользователю сообщение, попал он или нет.
            if is_ship:
                self.bot.send_message(self.leading.object.id, 'Вы попали.')
            else:
                self.bot.send_message(self.leading.object.id, 'Вы не попали.')

            # Если игрок проиграл, то отправляем соответствующее сообщение и удаляем его из сессии.
            ...

            # Изменяем ведущего игрока.
            self.change_leading()

    def get_opponent(self, player: Player) -> Player:
        """
        Получение следующего игрока в списке.
        """
        if player == self.players[-1]:
            return self.players[0]

        ind = self.players.index(player)
        return self.players[ind + 1]

    def ask_for_a_position(self) -> None:
        """
        Отправка игроку сообщения о предложении выбрать клетку.
        """
        self.bot.send_message(self.leading, 'Выберите клетку.')

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
        self.check_number_of_players()

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
            winner_state.in_game = False

            self.bot.send_message(winner.object.id, 'Поздравляем, вы выиграли!')

        self.stop_session()

    def check_number_of_players(self):
        """
        Проверка числа игроков в сессии.

        Если игроков в сессии меньше 2, то заканчиваем игру и подводим итоги.
        """
        if len(self.players) < 2:
            self.finish_game()

    def stop_session(self) -> None:
        """
        Завершение сессии.

        Завершаем цикл, изменив self.is_running на False.
        """
        self.is_running = False
