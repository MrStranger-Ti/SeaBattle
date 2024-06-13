from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from objects.player import row_letters, col_numbers


def get_positions_keyboard() -> InlineKeyboardMarkup:
    """
    Создание клавиатуры для позиций.

    :return: клавиатура
    """
    keyboard = InlineKeyboardMarkup()
    choices = []
    for row in row_letters:
        for col in col_numbers:
            choices.append(row + col)

    buttons = []
    for position in choices:
        button = InlineKeyboardButton(text=position, callback_data=position)
        buttons.append(button)

    size = len(row_letters)
    for _ in range(size):
        keyboard.row(*buttons[:size])
        del buttons[:size]

    return keyboard


def get_direction_keyboard() -> InlineKeyboardMarkup:
    """
    Создание клавиатуры для направлений.

    :return: клавиатура
    """
    keyboard = InlineKeyboardMarkup()
    choices = [
        ('влево', 'left'),
        ('вправо', 'right'),
        ('вверх', 'top'),
        ('вниз', 'bottom'),
        ('назад', 'cancel'),
    ]
    buttons = []
    for text, data in choices:
        button = InlineKeyboardButton(text=text, callback_data=data)
        buttons.append(button)

    keyboard.row(buttons[0], buttons[1])
    keyboard.row(buttons[2], buttons[3])
    keyboard.row(buttons[4])

    return keyboard
