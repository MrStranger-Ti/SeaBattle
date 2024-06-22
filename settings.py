import os.path
from string import ascii_uppercase, digits


# Основные настройки.
BASE_DIR = os.path.dirname(__file__)
DATABASE_PATH = os.path.join(BASE_DIR, 'database.db')


# Очередь игроков.
PLAYERS_QUEUE = []


# Названия кораблей.
SHIPS = [
    'first_3',
    'second_3',
    'first_2',
    'second_2',
    'third_2',
    'fourth_2',
    'first_1',
    'second_1',
]


# Строки поля.
ROW_LETTERS = ascii_uppercase[:8]

# Колонки поля.
COL_NUMBERS = digits[1: 9]


# Состояния.
STATES = dict()
