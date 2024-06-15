from telebot import TeleBot
from telebot.types import Message
from main import check_queue
from objects.collections import PLAYERS_QUEUE
from states.states import get_or_add_state
from keyboards.reply.main_keyboard import keyboard_start, keyboard_play


def load(bot: TeleBot):
    @bot.message_handler(commands=['info'])
    def info(message: Message):
        """
        Обработчик команды /info.

        :param message: сообщение
        """
        players_queue_ids = [user.id for user in PLAYERS_QUEUE]
        user_state = get_or_add_state(message.from_user.id)
        if message.from_user.id not in players_queue_ids and not user_state.in_game:
            with open('message_text/information.txt', 'r', encoding='utf-8') as f:  # открываем документ
                contents = f.read()
                bot.send_message(message.chat.id,contents)

    @bot.message_handler(commands=['start'])
    def start(message: Message):
        """
        Обработчик команды /start.

        :param message: сообщение
        """
        players_queue_ids = [user.id for user in PLAYERS_QUEUE]
        user_state = get_or_add_state(message.from_user.id)

        if message.from_user.id not in players_queue_ids and not user_state.in_game:
           bot.send_message(message.chat.id, text="Привет, {0.first_name}!".format(message.from_user), reply_markup=keyboard_start())
    @bot.message_handler(commands=['play'])
    def add_player_to_queue(message: Message):
        """
        Обработчик команды /play.

        :param message: сообщение
        """
        # Получаем все id игроков, которые находятся в очереди.
        players_queue_ids = [user.id for user in PLAYERS_QUEUE]

        # Достаем состояние пользователя.
        user_state = get_or_add_state(message.from_user.id)

        # Если пользователь не в очереди и не в игре, то добавляем его очередь.
        if message.from_user.id not in players_queue_ids and not user_state.in_game:
            PLAYERS_QUEUE.append(message.from_user)
            bot.send_message(message.from_user.id, 'Идет подбор игроков...', reply_markup=keyboard_play())
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

        :param message: сообщение
        """
        user_state = get_or_add_state(message.from_user.id)

        # Если игрок находится в игре, то ставим ему состояние leaving_game.
        # После этого сессия увидит, что у игрока сменилось состояние и исключит его.
        if user_state.in_game:
            user_state.name = 'leaving_game'


        # Если игрок находится в очереди подбора игроков, то удаляем его из очереди.
        for user in PLAYERS_QUEUE:
            if message.from_user.id == user.id:
                PLAYERS_QUEUE.remove(user)
                bot.send_message(message.from_user.id, 'Подбор игроков отменен.', reply_markup=keyboard_start())
                break

    @bot.message_handler(content_types=['text'])
    def text(message):
        if message.text == "Подбор игроков":
            add_player_to_queue(message)
            bot.delete_message(message_id=message.id, chat_id=message.from_user.id)
        elif message.text == "Покинуть очередь или игру":
            leave(message)
            bot.delete_message(message_id=message.id, chat_id=message.from_user.id)
        elif message.text == "Информация":
            info(message)
            bot.delete_message(message_id=message.id, chat_id=message.from_user.id)


