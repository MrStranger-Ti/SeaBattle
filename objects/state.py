import functools
from typing import Callable

from telebot import TeleBot
from telebot.types import Message, User

from settings import STATES


class State:
    """
    Объект состояния.

    Он хранит текущее состояние пользователя.

    Attributes:
        name (str): название
        in_game (bool): в игре ли пользователь
        messages (dict[str: str]): объект сообщения из библиотеки telebot
    """

    def __init__(self, bot: TeleBot, user: User, name: str, in_game: bool = False, buffer_count: int = 1):
        self.bot: TeleBot = bot
        self.user: User = user
        self.message_storage: dict[str: str] = dict()
        self.in_game: bool = in_game
        self._name: str = name
        self._buffer_count: int = buffer_count
        self._buffer_messages: list[int: Message] = list()

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def buffer_count(self) -> int:
        return self._buffer_count

    @buffer_count.setter
    def buffer_count(self, value: int) -> None:
        self._buffer_count = value

    def add_buffer_message(self, message: Message) -> None:
        self._buffer_messages.append(message)
        if len(self._buffer_messages) > self._buffer_count:
            self._delete_messages()

    def _delete_messages(self) -> None:
        moving_messages_ids = [message.id for message in self._buffer_messages[:-self._buffer_count]]
        deleted = self.bot.delete_messages(self.user.id, moving_messages_ids)
        if deleted:
            del self._buffer_messages[:-self._buffer_count]


def get_state(user_id: int) -> State:
    return STATES.get(user_id)


def init(bot: TeleBot) -> Callable:
    def preparatory_decorator(func: Callable):
        @functools.wraps(func)
        def decorator(message: Message, *args, **kwargs):
            if message.from_user.id not in STATES:
                STATES[message.from_user.id] = State(bot, message.from_user, 'main')

            result = func(message, *args, **kwargs)
            return result

        return decorator

    return preparatory_decorator
