import telebot.types

STATES: dict[int: 'State'] = {}


class State:
    def __init__(self, name, message: telebot.types.Message | None = None):
        self.name = name
        self.message = message


def add_or_update_state(user_id: int, name: str, message: telebot.types.Message = None) -> None:
    STATES[user_id] = State(name, message)


def remove_state(user_id: int) -> None:
    if user_id in STATES:
        STATES.pop(user_id)
