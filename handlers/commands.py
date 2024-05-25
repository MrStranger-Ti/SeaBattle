from telebot import TeleBot
from telebot.types import Message

from threads.matchmaking import PLAYERS_QUEUE, PLAYERS_IN_GAME


def load(bot: TeleBot):

    @bot.message_handler(commands=['stop'])
    def stop_polling(message: Message):
        bot.stop_polling()

    @bot.message_handler(commands=['play'])
    def add_player_to_queue(message: Message):
        if message.from_user.id not in PLAYERS_QUEUE and message.from_user.id not in PLAYERS_IN_GAME:
            bot.reply_to(message, 'Начинается подбор игроков')
            PLAYERS_QUEUE.append(message.from_user.id)

        elif message.from_user.id in PLAYERS_QUEUE:
            bot.reply_to(message, 'Вы уже в очереди')

        else:
            bot.reply_to(message, 'Вы уже в игре')

    @bot.message_handler(commands=['leave'])
    def leave(message: Message):
        if message.from_user.id in PLAYERS_QUEUE or message.from_user.id in PLAYERS_IN_GAME:

            if message.from_user.id in PLAYERS_QUEUE:
                PLAYERS_QUEUE.remove(message.from_user.id)
                bot.reply_to(message, 'Вы покинули очередь')

            else:
                PLAYERS_IN_GAME.remove(message.from_user.id)
                bot.reply_to(message, 'Вы покинули игру')
