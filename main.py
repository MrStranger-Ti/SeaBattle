import importlib
import logging
import os

import telebot.types

from loader import bot
from threads.session import Session

logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)


def create_session(players: list[telebot.types.User]):
    """
    Создание сессии.

    Если в очереди есть нужное количество игроков, то создаем сессию.
    """

    session = Session(bot, players)
    session.start()


def main():
    # подгружаем все файлы с обработчиками
    for file_name in os.listdir('./handlers/'):
        if file_name.endswith('.py') and file_name != '__init__.py':
            mod = importlib.import_module('handlers.' + file_name[:-3])
            mod.load(bot)

    from threads.matchmaking import start_matchmaking
    thread = start_matchmaking()

    logger.info('Бот запущен!')
    bot.infinity_polling()
    thread.run_cycle = False


if __name__ == '__main__':
    main()
