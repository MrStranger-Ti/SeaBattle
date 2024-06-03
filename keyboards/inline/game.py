from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_direction_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    choices = [
        ('влево', 'left'),
        ('вправо', 'right'),
        ('вверх', 'top'),
        ('вниз', 'bottom'),
    ]
    buttons = []
    for text, data in choices:
        button = InlineKeyboardButton(text, callback_data=data)
        buttons.append(button)

    keyboard.row(buttons[0], buttons[1])
    keyboard.row(buttons[2], buttons[3])

    return keyboard
