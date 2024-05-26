from telebot import TeleBot
from telebot.types import Message

from states.states import STATES, add_or_update_state, State


def load(bot: TeleBot):

    @bot.message_handler(content_types=['text'])
    def make_move(message: Message):
        user_state: State = STATES.get(message.from_user.id)

        if user_state.name == 'waiting_for_move':
            bot.delete_message(message.chat.id, message.id)

        elif user_state.name == 'making_move':
            add_or_update_state(
                user_id=message.from_user.id,
                name='check_move',
                message=message,
            )
