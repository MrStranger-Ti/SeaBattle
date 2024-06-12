import importlib
import logging
import os

import telebot.types
import dotenv

from database.queries import create_tables
from loader import bot
from objects.collections import PLAYERS_QUEUE
from states.states import get_or_add_state
from threads.session import Session

dotenv.load_dotenv()


logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)


def check_queue() -> None:
    """
    Проверка очереди игроков.

    После того как пользователь ввел команду /play, проверяем очередь.
    Если игроков достаточное количество, то запускаем с ними сессию.
    """
    # total_players - количество необходимых игроков для создания сессии.
    total_players = int(os.getenv('TOTAL_SESSION_PLAYERS', 4))
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
    Создание и запуск сессии.
    """
    session = Session(bot, players)
    session.start()


def main():
    # подгружаем все файлы с обработчиками.
    for file_name in os.listdir('./handlers/'):
        if file_name.endswith('.py') and file_name != '__init__.py':
            mod = importlib.import_module('handlers.' + file_name[:-3])
            mod.load(bot)

    # создаем таблицы, если их еще нет.
    create_tables()

    logger.info('Бот запущен!')
    bot.infinity_polling()


if __name__ == '__main__':
    main()
