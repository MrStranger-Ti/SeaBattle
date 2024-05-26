from telebot import TeleBot
from telebot.types import Message

from threads.matchmaking import PLAYERS_QUEUE, PLAYERS_IN_GAME


def load(bot: TeleBot):

    @bot.message_handler(commands=['stop'])
    def stop_polling(message: Message):
        bot.stop_polling()

    @bot.message_handler(commands=['play'])
    def add_player_to_queue(message: Message):
        players_queue_ids = [user.id for user in PLAYERS_QUEUE]
        players_in_game_ids = [user.id for user in PLAYERS_IN_GAME]
        if message.from_user.id not in players_queue_ids and message.from_user.id not in players_in_game_ids:
            bot.reply_to(message, 'Начинается подбор игроков')
            PLAYERS_QUEUE.append(message.from_user)
            print(PLAYERS_QUEUE)
            print(PLAYERS_IN_GAME)

        elif message.from_user.id in [user.id for user in PLAYERS_QUEUE]:
            bot.reply_to(message, 'Вы уже в очереди')

        else:
            bot.reply_to(message, 'Вы уже в игре')

    @bot.message_handler(commands=['leave'])
    def leave(message: Message):
        if message.from_user.id in PLAYERS_QUEUE or message.from_user.id in PLAYERS_IN_GAME:

            if message.from_user.id in PLAYERS_QUEUE:
                PLAYERS_QUEUE.pop(message.from_user.id)
                bot.reply_to(message, 'Вы покинули очередь')

            else:
                PLAYERS_IN_GAME.pop(message.from_user.id)
                bot.reply_to(message, 'Вы покинули игру')
