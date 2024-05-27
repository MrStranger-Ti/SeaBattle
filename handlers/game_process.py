from telebot import TeleBot
from telebot.types import Message

from states.states import get_or_add_state


def load(bot: TeleBot):
    @bot.message_handler(content_types=['text'])
    def make_move(message: Message):
        """
        Обработчик обычного сообщения.
        """
        # Достаем состояние пользователя.
        user_state = get_or_add_state(message.from_user.id)

        # Если состояние waiting_for_move, то удаляем его сообщения, чтобы не засорять чат.
        if user_state.name == 'waiting_for_move':
            bot.delete_message(message.chat.id, message.id)

        # Если состояние making_move, то меняем состояние на check_move
        # и сохраняем сообщение в объекте состояния для последующей обработки в сессии.
        elif user_state.name == 'making_move':
            user_state.name = 'check_move'
            user_state.message = message
