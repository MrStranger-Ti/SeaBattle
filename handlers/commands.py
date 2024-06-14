from telebot import TeleBot
from telebot.types import Message
from telebot import types
from main import check_queue
from objects.collections import PLAYERS_QUEUE
from states.states import get_or_add_state


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
            with open("information.txt", "rb") as f:  # открываем документ
                contents = f.read().decode("UTF-8")
                bot.send_message(message.chat.id,contents)
                bot.delete_message(message_id=message.id,chat_id=message.from_user.id)
            

    @bot.message_handler(commands=['start'])
    def start(message: Message):

        """
        Обработчик команды /start.

        :param message: сообщение
        """

        players_queue_ids = [user.id for user in PLAYERS_QUEUE]
        user_state = get_or_add_state(message.from_user.id)

        if message.from_user.id not in players_queue_ids and not user_state.in_game:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton("Подбор игроков")
            btn2 = types.KeyboardButton("Информация")
            markup.add(btn1, btn2)
            bot.send_message(message.chat.id,text="Привет, {0.first_name}!".format(message.from_user), reply_markup=markup)

    @bot.message_handler(commands=['play'])
    def add_player_to_queue(message: Message):

        """
        Обработчик команды /play.

        :param message: сообщение
        """

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Покинуть очередь или игру")
        markup.add(btn1)

        # Получаем все id игроков, которые находятся в очереди.
        players_queue_ids = [user.id for user in PLAYERS_QUEUE]

        # Достаем состояние пользователя.
        user_state = get_or_add_state(message.from_user.id)

        # Если пользователь не в очереди и не в игре, то добавляем его очередь.
        if message.from_user.id not in players_queue_ids and not user_state.in_game:
            PLAYERS_QUEUE.append(message.from_user)
            bot.send_message(message.from_user.id, 'Идет подбор игроков...' , reply_markup=markup)

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

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Подбор игроков")
        btn2 = types.KeyboardButton("Правила")
        markup.add(btn1, btn2)

        user_state = get_or_add_state(message.from_user.id)

        # Если игрок находится в игре, то ставим ему состояние leaving_game.
        # После этого сессия увидит, что у игрока сменилось состояние и исключит его.
        if user_state.in_game:
            user_state.name = 'leaving_game'


        # Если игрок находится в очереди подбора игроков, то удаляем его из очереди.
        for user in PLAYERS_QUEUE:
            if message.from_user.id == user.id:
                PLAYERS_QUEUE.remove(user)
                bot.send_message(message.from_user.id, 'Подбор игроков отменен.', reply_markup=markup)
                break

    @bot.message_handler(content_types=['text'])
    def text(message):
        if message.text == "Подбор игроков":
            add_player_to_queue(message)
        if message.text == "Покинуть очередь или игру":
            leave(message)
        if message.text == "Информация":
            info(message)
