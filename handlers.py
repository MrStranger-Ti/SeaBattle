from telebot import TeleBot
from telebot.types import Message, CallbackQuery

from helpers.deleting_messages import deleting_user_messages
from helpers.sending_messages import send_message
from database.queries import get_users
from helpers.validators import validate_positions_callback
from objects.state import init, get_state
from settings import PLAYERS_QUEUE, SHIPS, STATES
from keyboards.reply.main_keyboard import keyboard_start, keyboard_play
from threads.session import check_queue


def load(bot: TeleBot):
    # |--------------------|
    # | Обработчики команд |
    # |--------------------|
    @bot.message_handler(commands=['info'])
    @deleting_user_messages(bot)
    @init(bot)
    def info(message: Message):
        """
        Обработчик команды /info.

        :param message: сообщение
        """
        players_queue_ids = [user.id for user in PLAYERS_QUEUE]
        user_state = get_state(message.from_user.id)
        if message.from_user.id not in players_queue_ids and not user_state.in_game:
            with open('message_text/information.txt', 'r', encoding='utf-8') as f:  # открываем документ
                contents = f.read()
                send_message(bot, message.from_user.id, contents, reply_markup=keyboard_start())

    @bot.message_handler(commands=['rating'])
    @deleting_user_messages(bot)
    @init(bot)
    def rating_table(message: Message):
        """
        Обработчик команды /rating.

        :param message: сообщение
        """
        players_queue_ids = [user.id for user in PLAYERS_QUEUE]
        user_state = get_state(message.from_user.id)

        if message.from_user.id not in players_queue_ids and not user_state.in_game:
            users_rating = ""
            current_user_rating = None
            for num, user in enumerate(get_users(), start=1):
                user_id, username, rating = user
                if num <= 10:
                    users_rating += f"{num}. @{username} - {rating}🏆\n"

                if user_id == message.from_user.id:
                    current_user_rating = f"\n<b>{num}. @{username}(вы) - {rating}🏆</b>\n"

            if current_user_rating:
                users_rating += current_user_rating

            send_message(
                bot,
                message.chat.id,
                text=f"🏵Таблица лидеров🏵\n\n{users_rating}",
                reply_markup=keyboard_start(),
                parse_mode="HTML",
            )

    @bot.message_handler(commands=['start'])
    @deleting_user_messages(bot)
    @init(bot)
    def start(message: Message):
        """
        Обработчик команды /start.

        :param message: сообщение
        """
        players_queue_ids = [user.id for user in PLAYERS_QUEUE]
        user_state = get_state(message.from_user.id)

        if message.from_user.id not in players_queue_ids and not user_state.in_game:
            send_message(
                bot,
                message.chat.id,
                text="Привет, {0.first_name}!".format(message.from_user),
                reply_markup=keyboard_start(),
            )

    @bot.message_handler(commands=['play'])
    @deleting_user_messages(bot)
    @init(bot)
    def add_player_to_queue(message: Message):
        """
        Обработчик команды /play.

        :param message: сообщение
        """
        # Получаем все id игроков, которые находятся в очереди.
        players_queue_ids = [user.id for user in PLAYERS_QUEUE]

        # Достаем состояние пользователя.
        user_state = get_state(message.from_user.id)

        # Если пользователь не в очереди и не в игре, то добавляем его очередь.
        if message.from_user.id not in players_queue_ids and not user_state.in_game:
            PLAYERS_QUEUE.append(message.from_user)
            send_message(
                bot,
                message.from_user.id,
                'Идет подбор игроков...',
                reply_markup=keyboard_play(),
            )

            # Проверяем количество игроков в очереди и запускаем сессию с нужным количеством игроков.
            check_queue(bot)

        # Если пользователь в очереди, то уведомляем его об этом.
        elif message.from_user.id in players_queue_ids:
            send_message(bot, message.from_user.id, 'Вы уже в очереди.')

        # Если пользователь в игре, то уведомляем его об этом.
        elif user_state.in_game:
            send_message(bot, message.from_user.id, 'Вы уже в игре.')

    @bot.message_handler(commands=['leave'])
    @deleting_user_messages(bot)
    @init(bot)
    def leave(message: Message):
        """
        Обработчик команды /leave.

        :param message: сообщение
        """
        user_state = get_state(message.from_user.id)

        # Если игрок находится в игре, то ставим ему состояние leaving_game.
        # После этого сессия увидит, что у игрока сменилось состояние и исключит его.
        if user_state.in_game:
            user_state.name = 'leaving_game'

        # Если игрок находится в очереди подбора игроков, то удаляем его из очереди.
        for user in PLAYERS_QUEUE:
            if message.from_user.id == user.id:
                PLAYERS_QUEUE.remove(user)
                send_message(
                    bot,
                    message.from_user.id,
                    'Подбор игроков отменен.',
                    reply_markup=keyboard_start(),
                )
                break

    # |-------------------------------|
    # | Обработчики встроенных кнопок |
    # |-------------------------------|
    @bot.callback_query_handler(validate_positions_callback)
    def process_position_buttons(callback: CallbackQuery):
        """
        Обработчик кнопок позиций ячеек.

        :param callback: данные о кнопке
        """
        user_state = get_state(callback.from_user.id)
        for ship in SHIPS:

            # Обработка позиции при подготовке к игре.
            if user_state.name == 'setting_ship_position_' + ship:
                user_state.name = 'check_ship_position_' + ship
                user_state.message_storage['position'] = callback.data

            # Обработка позиции в процессе игры.
            elif user_state.name == 'making_move':
                user_state.name = 'check_move'
                user_state.message_storage['position'] = callback.data

    @bot.callback_query_handler(lambda callback: callback.data in ('top', 'right', 'bottom', 'left', 'cancel'))
    def process_direction_buttons(callback: CallbackQuery):
        """
        Обработчик кнопок направления.

        :param callback: данные о кнопке
        """
        user_state = get_state(callback.from_user.id)
        for ship in SHIPS:

            # Обработка направления при подготовке к игре.
            if user_state.name == 'setting_ship_direction_' + ship:

                if callback.data == 'cancel':
                    user_state.name = 'cancel_ship_direction_' + ship
                    break

                user_state.name = 'check_ship_direction_' + ship
                user_state.message_storage['direction'] = callback.data

    # |-------------------|
    # | Обработчик текста |
    # |-------------------|
    @bot.message_handler(content_types=['text'])
    @deleting_user_messages(bot)
    @init(bot)
    def game_process(message: Message):
        """
        Обработчик обычного сообщения.

        :param message: сообщение
        """
        if message.text == "👥Подбор игроков👥":
            add_player_to_queue(message)

        elif message.text == "Покинуть очередь или игру":
            leave(message)

        elif message.text == "📕Информация📕":
            info(message)

        elif message.text == "🏆Рейтинг🏆":
            rating_table(message)
