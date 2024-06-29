import functools
from typing import Callable

from telebot import TeleBot
from telebot.apihelper import ApiTelegramException
from telebot.types import Message


def delete_user_message(bot: TeleBot, chat_id: int, message_id: int) -> bool:
    try:
        bot.delete_message(chat_id, message_id)
    except ApiTelegramException as exc:
        return False

    return True


def deleting_user_messages(bot: TeleBot) -> Callable:
    def preparatory_decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def decorator(message: Message, *args, **kwargs):
            delete_user_message(bot, message.from_user.id, message.id)
            result = func(message, *args, **kwargs)
            return result

        return decorator

    return preparatory_decorator
