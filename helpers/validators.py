from telebot.types import CallbackQuery

from settings import ROW_LETTERS, COL_NUMBERS


def validate_positions_callback(callback: CallbackQuery) -> bool:
    """
    Валидация позиции.

    :param callback: данные о кнопке
    :return: bool
    """
    positions = []
    for row in ROW_LETTERS:
        for col in COL_NUMBERS:
            positions.append(row + col)

    if callback.data in positions:
        return True
    return False
