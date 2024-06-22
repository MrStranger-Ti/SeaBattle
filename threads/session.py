import os
import random
import threading
import time
from typing import Optional, Any, Callable

import telebot
from telebot.types import Message

from database.queries import update_or_add_rating
from helpers.sending_messages import send_message, send_photo
from keyboards.inline.game import get_direction_keyboard, get_positions_keyboard
from objects.state import get_state
from settings import SHIPS, STATES, PLAYERS_QUEUE
from objects.exceptions import PositionError, CellOpenedError, ShipNearbyError
from objects.player import Player
from keyboards.reply.main_keyboard import keyboard_start


class Session(threading.Thread):
    """
    Сессия игры.

    При каждом запуске игры создается сессия, в которой идет игра до какого-то результата.

    Attributes:
        running (bool): выполняться ли потоку (сессию)
        bot (telebot.TeleBot): основной объект бота из библиотеки telebot
        players (list[Player]): список из игроков
        leading (Player): ведущий игрок
        total_players (int): количество игроков, участвующих в игре
        message_pool (dict[str: list[Message]]): пул сообщений для отправки
    """

    def __init__(self, bot: telebot.TeleBot, players: list[telebot.types.User]):
        super().__init__()
        self.running: bool = True
        self.bot: telebot.TeleBot = bot
        self.players: list[Player] = [Player(user) for user in players]
        self.spectators: list[Player] = list()
        self.leading: Optional[Player] = None
        self.total_players: int = len(players)
        self.message_pool: dict[str: list[tuple[Any]]] = dict()

    def run(self) -> None:
        # подготовка к игре
        self.prepare()

        # запуск игры
        if self.running:
            self.start_game()

        # контроль игры
        self.update()

    def send_message(self, player: Player, *args, **kwargs) -> None:
        self.add_sending_to_pool(player, send_message, args, kwargs)

    def send_photo(self, player: Player, *args, **kwargs) -> None:
        self.add_sending_to_pool(player, send_photo, args, kwargs)

    def add_sending_to_pool(self, player: Player, func: Callable, args: tuple[Any], kwargs: dict['str': Any]) -> None:
        player_message_pool = self.message_pool.setdefault(player.object.id, list())
        player_message_pool.append((func, args, kwargs))

    def send_player_pool(self, player: Player) -> None:
        player_message_pool = self.message_pool.get(player.object.id)
        if player_message_pool:
            self.change_player_buffer(player, len(player_message_pool))
            for func, args, kwargs in player_message_pool:
                func(self.bot, player.object.id, *args, **kwargs)
                time.sleep(0.3)

            player_message_pool.clear()

    def send_pool(self) -> None:
        for player in self.players + self.spectators:
            self.send_player_pool(player)

    @staticmethod
    def change_player_buffer(player: Player, buffer_count: int) -> None:
        player_state = get_state(player.object.id)
        player_state.buffer_count = buffer_count

    def prepare(self) -> None:
        """
        Подготовка к игре.
        """
        # Просим всех игроков установить первый корабль.
        for player in self.players:
            player_state = get_state(player.object.id)
            player_state.name = 'setting_ship_position_' + SHIPS[0]
            self.ask_to_set_the_ship(player, SHIPS[0])

        # Пока все не будут готовы к игре, игра не начнется.
        while not self.is_everyone_ready():
            time.sleep(0.1)

            self.send_pool()
            self.check_leaving_players()

            for player in self.players:
                player_state = get_state(player.object.id)
                position = player_state.messages.get('position')
                direction = player_state.messages.get('direction')
                for count, ship in enumerate(SHIPS):
                    if player_state.name == 'check_ship_position_' + ship:
                        try:
                            cell = player.get_cell(position)
                        except PositionError:
                            self.ask_to_set_the_ship(player, ship)
                            self.send_message(player, 'Неверная клетка')
                            player_state.name = 'setting_ship_position_' + ship
                            break

                        if not player.valid_cell(cell):
                            player_state.name = 'setting_ship_position_' + ship
                            self.ask_to_set_the_ship(player, ship)
                            self.send_message(player, 'Нельзя поставить корабль рядом с другим. Попробуйте снова.')
                            break

                        if player_state.name.endswith('1'):
                            try:
                                player.set_ship(position, ship)
                            except ShipNearbyError:
                                player_state.name = 'setting_ship_position_' + ship
                                self.ask_to_set_the_ship(player, ship)
                                self.send_error(player.object.id, 'Нельзя поставить корабль рядом с другим. Попробуйте снова.')

                            if player.all_ships_on_field():
                                player.ready = True
                                player_state.name = 'waiting_for_players'
                                self.send_photo(
                                    player,
                                    player.draw_player_field(),
                                    caption='Вы готовы к игре. Дождитесь всех игроков.',
                                )
                            else:
                                next_ship = SHIPS[count + 1]
                                player_state.name = 'setting_ship_position_' + next_ship
                                self.ask_to_set_the_ship(player, next_ship)
                        else:
                            player_state.name = 'setting_ship_direction_' + ship
                            self.ask_to_choose_a_direction(player, position)

                    elif player_state.name == 'check_ship_direction_' + ship:
                        try:
                            player.set_ship(position, ship, direction=direction)
                        except (PositionError, ShipNearbyError, ValueError) as exc:
                            player_state.name = 'setting_ship_direction_' + ship
                            self.ask_to_choose_a_direction(player, position)

                            if isinstance(exc, PositionError):
                                self.send_message(player, 'Нельзя поставить корабль на несуществующую клетку. Попробуйте снова.')

                            elif isinstance(exc, ShipNearbyError):
                                self.send_message(player, 'Нельзя поставить корабль рядом с другим. Попробуйте снова.')

                            elif isinstance(exc, ValueError):
                                self.send_message(player, 'Передано неверное направление.')

                            break

                        next_ship = SHIPS[count + 1]
                        player_state.name = 'setting_ship_position_' + next_ship
                        self.ask_to_set_the_ship(player, next_ship)

                    elif player_state.name == 'cancel_ship_direction_' + ship:
                        player_state.name = 'setting_ship_position_' + ship
                        self.ask_to_set_the_ship(player, ship)

    def ask_to_set_the_ship(self, player: Player, ship_name: str) -> None:
        """
        Предлагаем игроку выбрать ячейку для установки корабля.

        :param player: игрок
        :param ship_name: название корабля в списке ships
        """
        self.send_photo(
            player,
            player.draw_player_field(),
        )
        self.send_message(
            player,
            f'Установка {ship_name[-1]} размерного корабля',
            reply_markup=get_positions_keyboard(player),
        )

    def ask_to_choose_a_direction(self, player: Player, position: str) -> None:
        """
        Просим игрока выбрать направление.

        :param player: игрок
        :param position: позиция
        """
        self.send_photo(
            player,
            player.draw_player_field(marked_position=position),
        )

        self.send_message(
            player,
            f'Выберите направление для {position}',
            reply_markup=get_direction_keyboard(),
        )

    def start_game(self) -> None:
        """
        Запуск игры.
        """
        # Всем игрокам в сессии выставляем состояние waiting_for_move.
        for player in self.players:
            player.opponent = self.get_opponent(player)
            player_state = get_state(player.object.id)
            player_state.name = 'waiting_for_move'
            self.send_message(
                player,
                f'Игра начинается.\nВаш оппонент: {player.opponent}',
            )

        self.send_pool()

        # Засыпаем, чтобы игроки прочитали сообщение о старте игры.
        time.sleep(3)

        if self.players:
            # Случайным образом определяем ведущего игрока.
            self.leading = random.choice(self.players)

            # Выставляем ведущему игроку состояние making_move и просим сделать ход.
            leading_player_state = get_state(self.leading.object.id)
            leading_player_state.name = 'making_move'
            self.ask_to_make_a_move()

            # Предупреждаем игрока об атаке.
            self.warn_player_about_an_attack()

            self.send_pool()

    def update(self) -> None:
        """
        Обновление сессии.

        Здесь происходит проверка состояний всех игроков.
        Состояния ведущего игрока проверяются отдельно.
        """
        while self.running:
            time.sleep(0.3)

            self.check_leaving_players()

            # Получаем состояние ведущего игрока
            leading_player_state = get_state(self.leading.object.id)

            # Если у ведущего игрока состояние check_move, то пробуем раскрыть клетку у соперника.
            if leading_player_state.name == 'check_move':

                try:
                    # Пробуем открыть клетку соперника. Если мы успешно ее открыли, то узнаем корабль это или нет.
                    is_ship = self.leading.open_opponent_cell(leading_player_state.messages.get('position'))
                except (PositionError, CellOpenedError) as exc:
                    self.ask_to_make_a_move()

                    # Так как произошла ошибка, то меняем состояние на making_move,
                    # чтобы игрок смог попробовать еще раз сделать ход.
                    leading_player_state.name = 'making_move'

                    # Если клетки, который ввел пользователь, не существует,
                    # то отправляем ему соответствующее сообщение.
                    if isinstance(exc, PositionError):
                        self.send_message(self.leading, 'Неверная клетка.')

                    # Если клетка, который ввел пользователь, уже открыта,
                    # то отправляем ему соответствующее сообщение.
                    elif isinstance(exc, CellOpenedError):
                        self.send_message(self.leading, 'Эта клетка уже открыта.')

                    self.send_player_pool(self.leading)
                    continue

                # Отправляем ведущему игроку поле противника.
                format_lead_message = 'Вы попали' if is_ship else 'Вы не попали'
                self.send_photo(
                    self.leading,
                    self.leading.draw_player_field(opponent=True),
                    caption=f'{format_lead_message} в корабль игрока {self.leading.opponent}',
                )

                # Отправляем противнику ведущего игрока свое поле.
                self.show_move_result_to_opponent(is_ship)

                # Отправляем поле оппонента ведущего игрока всем игрокам, чтобы они могли наблюдать за игрой, пока ждут свой ход.
                self.show_all_players_the_field(is_ship)

                # Если игрок проиграл, то отправляем соответствующее сообщение и удаляем его из сессии.
                opponent = self.leading.opponent
                if opponent.lost:
                    self.send_message(opponent, 'Вы проиграли.', reply_markup=keyboard_start())
                    self.move_player_to_spectators(opponent)

                # Изменяем ведущего игрока, если игроков в сессии больше одного и если он не попал,
                # иначе просим ведущего игрока сделать еще один ход.
                if len(self.players) > 1 and not is_ship:
                    self.change_leading()

                elif len(self.players) > 1:
                    leading_player_state.name = 'making_move'
                    self.ask_to_make_a_move(send_field=False)

            self.send_pool()

    def show_move_result_to_opponent(self, is_ship: bool) -> None:
        format_opponent_message = 'попал' if is_ship else 'не попал'
        self.send_photo(
            self.leading.opponent,
            self.leading.opponent.draw_player_field(),
            caption=f'Игрок {self.leading} {format_opponent_message} в ваш корабль',
        )

    def show_all_players_the_field(self, hit: bool) -> None:
        """
        Отправка состояния игры всем не участвующим игрокам.

        :param hit: было ли попадание
        """
        dynamic_text = 'попал' if hit else 'не попал'
        message_text = f'Игрок {self.leading} {dynamic_text} в корабль игрока {self.leading.opponent}'
        for player in self.players + self.spectators:
            if player not in (self.leading, self.leading.opponent):
                self.send_photo(
                    player,
                    self.leading.draw_player_field(opponent=True),
                    caption=message_text,
                )

    def check_leaving_players(self) -> None:
        """
        Проверка игроков, которые хотят выйти из игры.
        """

        for player in self.players:
            player_state = get_state(player.object.id)

            # Если игрок хочет покинуть игру, то удаляем его из сессии.
            if player_state.name == 'leaving_game':
                self.send_message(player, 'Вы покинули игру.', reply_markup=keyboard_start())
                self.remove_player(player)

    def is_everyone_ready(self) -> bool:
        """
        Проверка игроков на готовность.

        Если все готовы, то запускаем игру.

        :return bool
        """
        return all(player.ready for player in self.players)

    def ask_to_make_a_move(self, send_field: bool = True) -> None:
        """
        Отправка игроку сообщения о предложении выбрать клетку, а также отправка поля оппонента.

        :param send_field: отправлять ли ведущему игроку поле соперника
        """
        if send_field:
            # Отправка поля оппонента.
            self.send_photo(
                self.leading,
                self.leading.draw_player_field(opponent=True),
            )

        # Отправка клавиатуры для выбора ячейки.
        self.send_message(
            self.leading,
            f'Вы атакуете игрока {self.leading.opponent}',
            reply_markup=get_positions_keyboard(self.leading, opponent=True),
        )

    def change_leading(self) -> None:
        """
        Изменение ведущего игрока.

        Следующим ведущим игроком должен стать соперник текущего ведущего игрока.
        """
        # У старого ведущего игрока изменяем состояние на waiting_move
        old_leading_player_state = get_state(self.leading.object.id)
        old_leading_player_state.name = 'waiting_move'

        # Изменяем ведущего игрока
        self.leading = self.get_opponent(self.leading)

        # У нового ведущего игрока изменяем состояние на making_move
        new_leading_player_state = get_state(self.leading.object.id)
        new_leading_player_state.name = 'making_move'

        self.ask_to_make_a_move()
        self.warn_player_about_an_attack()

    def warn_player_about_an_attack(self):
        """
        Отправка сообщения оппоненту ведущего игрока о том, что его атакуют.
        :return:
        """
        self.send_message(
            self.leading.opponent,
            f'Вас атакует {self.leading}',
        )

    def get_opponent(self, player: Player) -> Player:
        """
        Получение следующего игрока в списке.

        :param player: игрок, относительно которого нужно получить оппонента
        :return объект игрока
        """
        if player == self.players[-1]:
            return self.players[0]

        ind = self.players.index(player)
        return self.players[ind + 1]

    def remove_player(self, removing_player: Player) -> None:
        if removing_player in self.players:
            self.players.remove(removing_player)

        elif removing_player in self.spectators:
            self.spectators.remove(removing_player)

        else:
            return

        # После удаления выставляем состояние пользователя на main и меняем флаг in_game на False.
        user_state = get_state(removing_player.object.id)
        user_state.name = 'main'
        user_state.in_game = False

        # Обновляем рейтинг игрока.
        self.update_rating(removing_player)

        # Отправляем пользователю итоги игры, а затем отправляем ему сообщение
        self.send_player_pool(removing_player)
        self.change_player_buffer(removing_player, buffer_count=1)

    def move_player_to_spectators(self, moving_player: Player) -> None:
        """
        Удаление игрока из сессии.

        :param moving_player: игрок, которого нужно удалить
        """
        # Перед удалением меняем оппонента у позади стоящего игрока.
        ind_back_player = self.players.index(moving_player) - 1
        back_player = self.players[ind_back_player]
        back_player.opponent = moving_player.opponent

        # Отправляем всем игрокам сообщение о том, что игрок проиграл или вышел из игры.
        for player in self.players + self.spectators:
            if player != moving_player:
                format_string = 'проиграл' if moving_player.lost else 'покинул игру'
                self.send_message(player, f'Игрок {moving_player} {format_string}')

        # Удаляем игрока.
        self.players.remove(moving_player)

        moving_player_state = get_state(moving_player.object.id)
        moving_player_state.name = 'watching_the_game'

        # Добавляем игрока в режим наблюдателя.
        self.spectators.append(moving_player)

        # Проверяем количество оставшихся игроков.
        self.check_number_of_players()

    def update_rating(self, player: Player) -> None:
        """
        Обновление рейтинга игрока.

        :param player: игрок
        """
        if self.total_players - 1 == len(self.players):
            player_rating = -1
        else:
            player_rating = self.total_players - len(self.players) - 1

        update_or_add_rating(player.object, player_rating)

    def check_number_of_players(self) -> None:
        """
        Проверка числа игроков в сессии.

        Если игроков в сессии меньше 2, то заканчиваем игру и подводим итоги.
        """
        if len(self.players) < 2:
            self.finish_game()

    def finish_game(self) -> None:
        """
        Подводим итоги игры.

        Единственному оставшемуся игроку в сессии отправляем поздравление,
        обновляем рейтинг, изменяем его состояние и завершаем сессию.
        """
        for player in self.spectators.copy():
            self.remove_player(player)

        if self.players:
            winner = self.players[0]
            self.send_message(winner, 'Поздравляем, вы выиграли!', reply_markup=keyboard_start())
            self.remove_player(winner)

        self.stop_session()

    def stop_session(self) -> None:
        """
        Завершение сессии.

        Завершаем цикл, изменив self.is_running на False.
        """
        self.running = False


def check_queue(bot: telebot.TeleBot) -> None:
    """
    Проверка очереди игроков.

    После того как пользователь ввел команду /play, проверяем очередь.
    Если игроков достаточное количество, то запускаем с ними сессию.
    """
    # total_players - количество необходимых игроков для создания сессии.
    total_players = int(os.getenv('TOTAL_SESSION_PLAYERS', 4))
    if len(PLAYERS_QUEUE) >= total_players:
        for player in PLAYERS_QUEUE[:total_players]:

            # Перед созданием сессии устанавливаем флаг in_game=True, чтобы знать, что пользователь в игре.
            state = get_state(player.id)
            state.in_game = True

        # Создаем сессию.
        create_session(bot, PLAYERS_QUEUE[:total_players])

        # Удаляем игроков из очереди, с которыми создали сессию.
        del PLAYERS_QUEUE[:total_players]


def create_session(bot: telebot.TeleBot, players: list[telebot.types.User]) -> None:
    """
    Создание и запуск сессии.
    """
    session = Session(bot, players)
    session.start()
