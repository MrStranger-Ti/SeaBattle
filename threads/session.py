import random
import threading
import time
from typing import Optional

import telebot
from telebot import types

from database.queries import update_or_add_rating
from keyboards.inline.game import get_direction_keyboard, get_positions_keyboard
from settings import ships
from objects.exceptions import PositionError, CellOpenedError, ShipNearbyError
from objects.player import Player
from states.states import get_or_add_state
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
    """

    def __init__(self, bot: telebot.TeleBot, players: list[telebot.types.User]):
        super().__init__()
        self.running: bool = True
        self.bot: telebot.TeleBot = bot
        self.players: list[Player] = [Player(user) for user in players]
        self.leading: Optional[Player] = None
        self.total_players: int = len(players)

    def run(self) -> None:
        # подготовка к игре
        self.prepare()

        # запуск игры
        if self.running:
            self.start_game()

        # контроль игры
        while self.running:
            time.sleep(1)
            self.update()

    def prepare(self) -> None:
        """
        Подготовка к игре.
        """
        # Просим всех игроков установить первый корабль.
        for player in self.players:
            player_state = get_or_add_state(player.object.id)
            player_state.name = 'setting_ship_position_' + ships[0]
            self.ask_to_set_the_ship(player, ships[0])

        # Пока все не будут готовы к игре, игра не начнется.
        while not self.is_everyone_ready():
            time.sleep(1)

            self.check_leaving_players()
            for player in self.players:
                player_state = get_or_add_state(player.object.id)
                position = player_state.messages.get('position')
                direction = player_state.messages.get('direction')
                for count, ship in enumerate(ships):
                    if player_state.name == 'check_ship_position_' + ship:
                        try:
                            cell = player.get_cell(position)
                        except PositionError:
                            self.bot.send_message(player.object.id, 'Неверная клетка')
                            player_state.name = 'setting_ship_position_' + ship
                            break

                        if not player.valid_cell(cell):
                            player_state.name = 'setting_ship_position_' + ship
                            self.bot.send_message(player.object.id, 'Нельзя поставить корабль рядом с другим. Попробуйте снова.')
                            break

                        if player_state.name.endswith('1'):
                            try:
                                player.set_ship(position, ship)
                            except ShipNearbyError:
                                player_state.name = 'setting_ship_position_' + ship
                                self.bot.send_message(player.object.id, 'Нельзя поставить корабль рядом с другим. Попробуйте снова.')

                            if player.all_ships_on_field():
                                player.ready = True
                                player_state.name = 'waiting_for_players'
                                self.bot.send_message(player.object.id, 'Вы готовы к игре. Дождитесь всех игроков.')
                                self.bot.send_photo(player.object.id, player.draw_player_field())
                            else:
                                next_ship = ships[count + 1]
                                player_state.name = 'setting_ship_position_' + next_ship
                                self.ask_to_set_the_ship(player, next_ship)
                        else:
                            player_state.name = 'setting_ship_direction_' + ship
                            self.bot.send_message(player.object.id, 'Выберите направление', reply_markup=get_direction_keyboard())

                    elif player_state.name == 'check_ship_direction_' + ship:
                        try:
                            player.set_ship(position, ship, direction=direction)
                        except (PositionError, ShipNearbyError, ValueError) as exc:
                            if isinstance(exc, PositionError):
                                self.bot.send_message(player.object.id, 'Нельзя поставить корабль на несуществующую клетку. Попробуйте снова.')

                            elif isinstance(exc, ShipNearbyError):
                                self.bot.send_message(player.object.id, 'Нельзя поставить корабль рядом с другим. Попробуйте снова.')

                            elif isinstance(exc, ValueError):
                                self.bot.send_message(player.object.id, 'Передано неверное направление.')

                            player_state.name = 'setting_ship_direction_' + ship
                            self.bot.send_message(player.object.id, 'Выберите направление', reply_markup=get_direction_keyboard())
                            break

                        next_ship = ships[count + 1]
                        player_state.name = 'setting_ship_position_' + next_ship
                        self.ask_to_set_the_ship(player, next_ship)

                    elif player_state.name == 'cancel_ship_direction_' + ship:
                        player_state.name = 'setting_ship_position_' + ship
                        self.ask_to_set_the_ship(player, ship)

        # Всем игрокам в сессии выставляем состояние waiting_for_move.
        for player in self.players:
            player.opponent = self.get_opponent(player)
            player_state = get_or_add_state(player.object.id)
            player_state.name = 'waiting_for_move'

        # Случайным образом определяем ведущего игрока.
        if self.players:
            self.leading = random.choice(self.players)

    def ask_to_set_the_ship(self, player: Player, ship_name: str) -> None:
        """
        Предлагаем игроку выбрать ячейку для установки корабля.

        :param player: игрок
        :param ship_name: название корабля в списке ships
        """
        self.bot.send_message(player.object.id, f'Установка {ship_name[-1]} размерного корабля')
        self.bot.send_photo(player.object.id, player.draw_player_field(), caption='Ваше поле')
        self.bot.send_message(player.object.id, 'Выберите клетку', reply_markup=get_positions_keyboard())

    def start_game(self) -> None:
        """
        Запуск игры.
        """
        for player in self.players:
            self.bot.send_message(player.object.id, 'Игра начинается.')
            self.bot.send_message(player.object.id, f'Ваш оппонент: {player.opponent}')

        # Выставляем ведущему игроку состояние making_move и просим сделать ход.
        leading_player_state = get_or_add_state(self.leading.object.id)
        leading_player_state.name = 'making_move'
        self.ask_to_make_a_move()

    def update(self) -> None:
        """
        Обновление сессии.

        Здесь происходит проверка состояний всех игроков.
        Состояния ведущего игрока проверяются отдельно.
        """
        self.check_leaving_players()

        # Получаем состояние ведущего игрока
        leading_player_state = get_or_add_state(self.leading.object.id)

        # Если у ведущего игрока состояние check_move, то пробуем раскрыть клетку у соперника.
        if leading_player_state.name == 'check_move':

            try:
                # Пробуем открыть клетку соперника. Если мы успешно ее открыли, то узнаем корабль это или нет.
                is_ship = self.leading.open_opponent_cell(leading_player_state.messages.get('position'))
            except (PositionError, CellOpenedError) as exc:

                # Так как произошла ошибка, то меняем состояние на making_move,
                # чтобы игрок смог попробовать еще раз сделать ход.
                leading_player_state.name = 'making_move'

                # Если клетки, который ввел пользователь, не существует,
                # то отправляем ему соответствующее сообщение.
                if isinstance(exc, PositionError):
                    self.bot.send_message(self.leading.object.id, 'Неверная клетка.')

                # Если клетка, который ввел пользователь, уже открыта,
                # то отправляем ему соответствующее сообщение.
                if isinstance(exc, CellOpenedError):
                    self.bot.send_message(self.leading.object.id, 'Эта клетка уже открыта.')

                self.ask_to_make_a_move()
                return

            # Отправляем пользователю сообщение, попал он или нет.
            if is_ship:
                self.bot.send_message(self.leading.object.id, 'Вы попали.')
            else:
                self.bot.send_message(self.leading.object.id, 'Вы не попали.')

            # Отправляем ведущему игроку поле противника.
            self.bot.send_photo(
                self.leading.object.id,
                self.leading.draw_player_field(opponent=True),
                caption=f'Поле {self.leading.opponent}',
            )

            # Отправляем противнику ведущего игрока свое поле.
            format_string = 'попал' if is_ship else 'не попал'
            self.bot.send_photo(
                self.leading.opponent.object.id,
                self.leading.opponent.draw_player_field(),
                caption=f'В вас {format_string} {self.leading}',
            )

            # Отправляем поле оппонента ведущего игрока всем игрокам, чтобы они могли наблюдать за игрой, пока ждут свой ход.
            self.show_all_players_the_field(is_ship)

            # Если игрок проиграл, то отправляем соответствующее сообщение и удаляем его из сессии.
            opponent = self.leading.opponent
            if opponent.lost:
                self.bot.send_message(opponent.object.id, 'Вы проиграли.',reply_markup=keyboard_start())
                self.remove_player(opponent)

            # Изменяем ведущего игрока, если игроков в сессии больше одного и если он не попал,
            # иначе просим ведущего игрока сделать еще один ход.
            if len(self.players) > 1 and not is_ship:
                self.change_leading()
            else:
                leading_player_state.name = 'making_move'
                self.ask_to_make_a_move()

    def show_all_players_the_field(self, hit: bool) -> None:
        """
        Отправка состояния игры всем не участвующим игрокам.

        :param hit: было ли попадание
        """
        dynamic_text = 'попал' if hit else 'не попал'
        message_text = f'Игрок {self.leading} {dynamic_text} в корабль игрока {self.leading.opponent}'
        for player in self.players:
            if player not in (self.leading, self.leading.opponent):
                self.bot.send_photo(
                    player.object.id,
                    self.leading.draw_player_field(opponent=True),
                    caption=message_text,
                )

    def check_leaving_players(self) -> None:
        """
        Проверка игроков, которые хотят выйти из игры.
        """

        for player in self.players:
            player_state = get_or_add_state(player.object.id)

            # Если игрок хочет покинуть игру, то удаляем его из сессии.
            if player_state.name == 'leaving_game':
                self.remove_player(player)
                self.bot.send_message(player.object.id, 'Вы покинули игру.',reply_markup=keyboard_start())

    def is_everyone_ready(self) -> bool:
        """
        Проверка игроков на готовность.

        Если все готовы, то запускаем игру.

        :return bool
        """
        return all(player.ready for player in self.players)

    def ask_to_make_a_move(self) -> None:
        """
        Отправка игроку сообщения о предложении выбрать клетку, а также отправка поля оппонента.
        """
        # Отправка поля оппонента.
        self.bot.send_photo(
            self.leading.object.id,
            self.leading.draw_player_field(opponent=True),
            caption=f'Поле {self.leading.opponent}',
        )

        # Отправка клавиатуры для выбора ячейки.
        self.bot.send_message(
            self.leading.object.id,
            'Выберите клетку.',
            reply_markup=get_positions_keyboard(),
        )

        # Отправка оппоненту о том, что его атакуют.
        self.bot.send_message(
            self.leading.opponent.object.id,
            f'Вас атакует {self.leading}',
        )

    def change_leading(self) -> None:
        """
        Изменение ведущего игрока.

        Следующим ведущим игроком должен стать соперник текущего ведущего игрока.
        """
        # У старого ведущего игрока изменяем состояние на waiting_move
        old_leading_player_state = get_or_add_state(self.leading.object.id)
        old_leading_player_state.name = 'waiting_move'

        # Изменяем ведущего игрока
        self.leading = self.get_opponent(self.leading)

        # У нового ведущего игрока изменяем состояние на making_move
        new_leading_player_state = get_or_add_state(self.leading.object.id)
        new_leading_player_state.name = 'making_move'
        self.ask_to_make_a_move()

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
        """
        Удаление игрока из сессии.

        :param removing_player: игрок, которого нужно удалить
        """
        # Перед удалением меняем оппонента у позади стоящего игрока.
        ind_back_player = self.players.index(removing_player) - 1
        back_player = self.players[ind_back_player]
        back_player.opponent = removing_player.opponent

        # Удаляем игрока.
        self.players.remove(removing_player)

        # Отправляем всем игрокам сообщение о том, что игрок проиграл или вышел из игры.
        for player in self.players:
            format_string = 'проиграл' if removing_player.lost else 'покинул игру'
            self.bot.send_message(player.object.id, f'Игрок {removing_player} {format_string}')

        # Обновляем рейтинг игрока.
        self.update_rating(player)

        # После удаления выставляем состояние пользователя на main и меняем флаг in_game на False.
        state = get_or_add_state(player.object.id)
        state.name = 'main'
        state.in_game = False

        # Проверяем количество оставшихся игроков.
        self.check_number_of_players()

    def update_rating(self, player: Player) -> None:
        """
        Обновление рейтинга игрока.

        :param player: игрок
        """
        player_rating = self.total_players - len(self.players)
        update_or_add_rating(player.object.id, player_rating)

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


        if self.players:
            winner = self.players[0]
            self.players.remove(winner)
            self.update_rating(winner)
            winner_state = get_or_add_state(winner.object.id)
            winner_state.name = 'main'
            winner_state.in_game = False
            self.bot.send_message(winner.object.id, 'Поздравляем, вы выиграли!', reply_markup=keyboard_start())

        self.stop_session()

    def stop_session(self) -> None:
        """
        Завершение сессии.

        Завершаем цикл, изменив self.is_running на False.
        """
        self.running = False
