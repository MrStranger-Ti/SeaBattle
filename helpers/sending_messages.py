from telebot import TeleBot

from settings import MESSAGE_BUFFER


def send_message(bot: TeleBot, chat_id: int, *args, **kwargs) -> None:
    bot_message = bot.send_message(chat_id, *args, **kwargs)
    user_buffer = MESSAGE_BUFFER.get(chat_id)
    user_buffer.add_message_id(chat_id, bot_message.id)
