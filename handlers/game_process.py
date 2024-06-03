from telebot import TeleBot
from telebot.types import Message, CallbackQuery

from states.states import get_or_add_state
from threads.session import ships


def load(bot: TeleBot):
    @bot.message_handler(content_types=['text'])
    def game_process(message: Message):
        """
        Обработчик обычного сообщения.
        """
        # Достаем состояние пользователя.
        user_state = get_or_add_state(message.from_user.id)

        for ship in ships:
            if user_state.name == 'setting_ship_position_' + ship:
                user_state.name = 'check_ship_position_' + ship
                user_state.messages['position'] = message.text

        # Если состояние waiting_for_move, то удаляем его сообщения, чтобы не засорять чат.
        if user_state.name == 'waiting_for_move':
            bot.delete_message(message.chat.id, message.id)

        # Если состояние making_move, то меняем состояние на check_move
        # и сохраняем сообщение в объекте состояния для последующей обработки в сессии.
        elif user_state.name == 'making_move':
            user_state.name = 'check_move'
            user_state.message = message

    @bot.callback_query_handler(lambda callback: callback.data in ('top', 'right', 'bottom', 'left'))
    def handle_direction_buttons(callback: CallbackQuery):
        user_state = get_or_add_state(callback.from_user.id)

        for ship in ships:
            if user_state.name == 'setting_ship_direction_' + ship:
                user_state.name = 'check_ship_direction_' + ship
                user_state.messages['direction'] = callback.data
