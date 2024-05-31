from telebot.types import Message

STATES: dict[int: 'State'] = {}


class State:
    """
    Объект состояния.

    Он хранит текущее состояние пользователя.

    Attributes:
        name (str): название
        in_game (bool): в игре ли пользователь
        message (Message): объект сообщения из библиотеки telebot
    """
    def __init__(self, name: str, in_game: bool = False, message: Message | None = None):
        self.name: str = name
        self.in_game: bool = in_game
        self.messages: dict[str: str] = {}


def get_or_add_state(user_id: int, name: str | None = None, in_game: bool = False, message: Message | None = None) -> State:
    """
    Получение или добавление состояния.

    Если у пользователя нет состояния, то по умолчанию будет установлено состояние main.

    :param user_id: id пользователя telegram
    :param name: название состояния, которое нужно установить, если у пользователя еще нет состояния
    :param in_game: в игре ли пользователь
    :param message: объект сообщения из библиотеки telebot
    :return:
    """
    if not name:
        name = 'main'

    if user_id not in STATES:
        STATES[user_id] = State(name, in_game, message)

    return STATES.get(user_id)
