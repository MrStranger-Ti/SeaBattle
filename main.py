import logging

import dotenv

from database.queries import create_tables
from loader import bot
from threads.message_scheduler import start_message_scheduler

dotenv.load_dotenv()

logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)


def main() -> None:
    # Подгружаем все файлы с обработчиками.
    from handlers import load
    load(bot)

    # Создаем таблицы, если их еще нет.
    create_tables()

    # Запускаем планировщик для очистки буфера.
    start_message_scheduler()

    logger.info('Бот запущен!')
    bot.infinity_polling()


if __name__ == '__main__':
    main()
