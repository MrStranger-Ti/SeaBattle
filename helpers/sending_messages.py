from telebot import TeleBot
from telebot.types import Message

from objects.state import get_state


def add_message_to_buffer(user_id: int, bot_message: Message) -> None:
    user_state = get_state(user_id)
    user_state.add_message(bot_message)


def send_message(bot: TeleBot, chat_id: int, *args, **kwargs) -> Message:
    bot_message = bot.send_message(chat_id, *args, **kwargs)
    add_message_to_buffer(chat_id, bot_message)
    return bot_message


def send_photo(bot: TeleBot, chat_id: int, *args, **kwargs) -> Message:
    bot_message = bot.send_photo(chat_id, *args, **kwargs)
    add_message_to_buffer(chat_id, bot_message)
    return bot_message
