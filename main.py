import importlib
import logging
import os

import telebot.types

from loader import bot
from states.states import get_or_add_state
from threads.session import Session

logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)

PLAYERS_QUEUE = []


def check_queue() -> None:
    """
    Проверка очереди игроков.

    После того как пользователь ввел команду /play, проверяем очередь.
    Если игроков достаточное количество, то запускаем с ними сессию.
    """
    # total_players - количество необходимых игроков для создания сессии.
    total_players = 1
    if len(PLAYERS_QUEUE) >= total_players:
        for player in PLAYERS_QUEUE[:total_players]:

            # Перед созданием сессии устанавливаем флаг in_game=True, чтобы знать, что пользователь в игре.
            state = get_or_add_state(player.id)
            state.in_game = True

        # Создаем сессию.
        create_session(PLAYERS_QUEUE[:total_players])

        # Удаляем игроков из очереди, с которыми создали сессию.
        del PLAYERS_QUEUE[:total_players]


def create_session(players: list[telebot.types.User]):
    """
    Создание сессии.
    """
    session = Session(bot, players)
    session.start()


def main():
    # подгружаем все файлы с обработчиками.
    for file_name in os.listdir('./handlers/'):
        if file_name.endswith('.py') and file_name != '__init__.py':
            mod = importlib.import_module('handlers.' + file_name[:-3])
            mod.load(bot)

    logger.info('Бот запущен!')
    bot.infinity_polling()


if __name__ == '__main__':
    main()
