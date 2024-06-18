import os.path
from string import ascii_uppercase

# Основные настройки.
BASE_DIR = os.path.dirname(__file__)
DATABASE_PATH = os.path.join(BASE_DIR, 'database.db')


# Очередь игроков.
PLAYERS_QUEUE = []


# Названия кораблей.
SHIPS: list[str] = [
    'first_3',
    'second_3',
    'first_2',
    'second_2',
    'third_2',
    'fourth_2'
    'first_1',
    'second_2',
]


# Строки поля.
ROW_LETTERS = ascii_uppercase[:8]

# Колонки поля.
COL_NUMBERS = [str(num) for num in range(1, 9)]


# Сообщения бота, которые нужно удалить
deleting_messages = dict()


# Состояния
STATES: dict[int: 'State'] = {}


# Буферизация
MESSAGE_BUFFER = dict()
