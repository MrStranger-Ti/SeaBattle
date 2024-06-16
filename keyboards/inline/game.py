from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from objects.player import Player


def get_positions_keyboard(player: Player, opponent: bool = False) -> InlineKeyboardMarkup:
    """
    Создание клавиатуры для позиций.

    :param player: игрок
    :param opponent: отображать ли поле кнопок как вражеское
    :return: клавиатура
    """
    keyboard = InlineKeyboardMarkup()
    for row in player.field:
        row_buttons = []
        for cell in row:
            if (opponent and cell.is_ship and cell.opened) or (not opponent and cell.is_ship):
                button_text = '🚢'

            elif opponent and cell.opened:
                button_text = ' '

            else:
                button_text = '🟦'

            button = InlineKeyboardButton(text=button_text, callback_data=cell.position)
            row_buttons.append(button)

        keyboard.row(*row_buttons)

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
