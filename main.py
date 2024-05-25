import importlib
import logging
import os

from telebot.types import User

from database.queries import save_user
from loader import bot

logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)


def start_game(player_ids: list[int]):
    """
    Запуск игры.

    Если в очереди есть нужно количество игроков, то запускаем игру
    """
    for player_id in player_ids:
        bot.send_message(player_id, 'Игра начинается.')


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
