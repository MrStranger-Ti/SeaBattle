import functools
from typing import Callable

from telebot import TeleBot
from telebot.types import Message

from settings import MESSAGE_BUFFER, STATES


class State:
    """
    Объект состояния.

    Он хранит текущее состояние пользователя.

    Attributes:
        name (str): название
        in_game (bool): в игре ли пользователь
        messages (dict[str: str]): объект сообщения из библиотеки telebot
    """

    def __init__(self, name: str, in_game: bool = False):
        self.name: str = name
        self.in_game: bool = in_game
        self.messages: dict[str: str] = {}


class MessageBuffer:
    def __init__(self, bot: TeleBot, buffer_count: int = 1):
        self.bot = bot
        self._buffer_count = buffer_count
        self._messages: dict[int: list[int]] = dict()

    @property
    def buffer_count(self):
        return self._buffer_count

    @buffer_count.setter
    def buffer_count(self, value: int) -> None:
        self._buffer_count = value

    @property
    def messages_ids(self):
        return self._messages

    def add_message_id(self, chat_id: int, message_id: int) -> None:
        bot_messages = self._messages.setdefault(chat_id, list())
        bot_messages.append(message_id)

        if len(bot_messages) > self._buffer_count:
            self._delete_messages(chat_id, bot_messages)

    def _delete_messages(self, chat_id: int, bot_messages: list[int]) -> None:
        moving_messages = bot_messages[:-self._buffer_count]
        self.bot.delete_messages(chat_id, moving_messages)
        del bot_messages[:-self._buffer_count]


def init(bot: TeleBot) -> Callable:
    def preparatory_decorator(func: Callable):
        @functools.wraps(func)
        def decorator(message: Message, *args, **kwargs):
            if message.from_user.id not in STATES:
                STATES[message.from_user.id] = State('main')

            MESSAGE_BUFFER.setdefault(message.from_user.id, MessageBuffer(bot))

            result = func(message, *args, **kwargs)
            return result

        return decorator

    return preparatory_decorator
