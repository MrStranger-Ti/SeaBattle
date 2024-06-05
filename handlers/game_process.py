from telebot import TeleBot
from telebot.types import Message, CallbackQuery

from objects.collections import ships
from objects.player import row_letters, col_numbers
from states.states import get_or_add_state


def load(bot: TeleBot):
    @bot.message_handler(content_types=['text'])
    def game_process(message: Message):
        """
        Обработчик обычного сообщения.

        :param message: сообщение
        """
        # Достаем состояние пользователя.
        user_state = get_or_add_state(message.from_user.id)

        # Если состояние waiting_for_move, то удаляем его сообщения, чтобы не засорять чат.
        if user_state.name == 'waiting_for_move':
            bot.delete_message(message.chat.id, message.id)

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

    @bot.callback_query_handler(validate_positions_callback)
    def handle_position_buttons(callback: CallbackQuery):
        """
        Обработчик кнопок позиций ячеек.

        :param callback: данные о кнопке
        """
        user_state = get_or_add_state(callback.from_user.id)
        for ship in ships:

            # Обработка позиции при подготовке к игре.
            if user_state.name == 'setting_ship_position_' + ship:
                user_state.name = 'check_ship_position_' + ship
                user_state.messages['position'] = callback.data

            # Обработка позиции в процессе игры.
            elif user_state.name == 'making_move':
                user_state.name = 'check_move'
                user_state.messages['position'] = callback.data

    @bot.callback_query_handler(lambda callback: callback.data in ('top', 'right', 'bottom', 'left'))
    def handle_direction_buttons(callback: CallbackQuery):
        """
        Обработчик кнопок направления.

        :param callback: данные о кнопке
        """
        user_state = get_or_add_state(callback.from_user.id)
        for ship in ships:

            # Обработка направления при подготовке к игре.
            if user_state.name == 'setting_ship_direction_' + ship:
                user_state.name = 'check_ship_direction_' + ship
                user_state.messages['direction'] = callback.data
