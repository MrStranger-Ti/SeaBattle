from telebot import TeleBot
from telebot.types import Message

from main import PLAYERS_QUEUE, check_queue
from states.states import get_or_add_state


def load(bot: TeleBot):
    @bot.message_handler(commands=['start'])
    def start(message: Message):
        """
        Обработчик команды /start.
        """
        bot.send_message(message.from_user.id, f'Привет, {message.from_user.first_name}!')

    @bot.message_handler(commands=['play'])
    def add_player_to_queue(message: Message):
        """
        Обработчик команды /play.
        """
        # Получаем все id игроков, которые находятся в очереди.
        players_queue_ids = [user.id for user in PLAYERS_QUEUE]

        # Достаем состояние пользователя.
        user_state = get_or_add_state(message.from_user.id)

        # Если пользователь не в очереди и не в игре, то добавляем его очередь.
        if message.from_user.id not in players_queue_ids and not user_state.in_game:
            PLAYERS_QUEUE.append(message.from_user)
            bot.send_message(message.from_user.id, 'Идет подбор игроков...')

            # Проверяем количество игроков в очереди и запускаем сессию с нужным количеством игроков.
            check_queue()

        # Если пользователь в очереди, то уведомляем его об этом.
        elif message.from_user.id in players_queue_ids:
            bot.send_message(message.from_user.id, 'Вы уже в очереди.')

        # Если пользователь в игре, то уведомляем его об этом.
        elif user_state.in_game:
            bot.send_message(message.from_user.id, 'Вы уже в игре.')

    @bot.message_handler(commands=['leave'])
    def leave(message: Message):
        """
        Обработчик команды /leave.
        """
        user_state = get_or_add_state(message.from_user.id)

        # Если игрок находится в игре, то ставим ему состояние leaving_game.
        # После этого сессия увидит, что у игрока сменилось состояние и исключит его.
        if user_state.in_game:
            user_state.name = 'leaving_game'
            bot.send_message(message.from_user.id, 'Вы покинули игру.')

        # Если игрок находится в очереди подбора игроков, то удаляем его из очереди.
        for user in PLAYERS_QUEUE:
            if message.from_user.id == user.id:
                PLAYERS_QUEUE.remove(user)
                bot.send_message(message.from_user.id, 'Подбор игроков отменен.')
                break
