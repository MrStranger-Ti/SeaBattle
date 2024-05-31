from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_direction_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    choices = [
        ('влево', 'left'),
        ('вверх', 'top'),
        ('вправо', 'right'),
        ('вниз', 'bottom'),
    ]
    for text, data in choices:
        button = InlineKeyboardButton(text, callback_data=data)
        keyboard.add(button)

    return keyboard
