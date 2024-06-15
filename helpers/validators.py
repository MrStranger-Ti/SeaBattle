from telebot.types import CallbackQuery

from settings import row_letters, col_numbers


def validate_positions_callback(callback: CallbackQuery) -> bool:
    """
    Валидация позиции.

    :param callback: данные о кнопке
    :return: bool
    """
    positions = []
    for row in row_letters:
        for col in col_numbers:
            positions.append(row + col)

    if callback.data in positions:
        return True
    return False
