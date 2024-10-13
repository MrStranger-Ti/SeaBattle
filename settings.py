import os.path

from string import ascii_uppercase, digits

from dotenv import load_dotenv

load_dotenv()


# Основные настройки.
BASE_DIR = os.path.dirname(__file__)
DATABASE_PATH = os.path.join(BASE_DIR, 'database.db')
TOTAL_SESSION_PLAYERS = os.getenv('TOTAL_SESSION_PLAYERS', 4)
CLEAR_BUFFER_TIME = int(os.getenv('CLEAR_BUFFER_TIME', 60 * 24))


# Очередь игроков.
PLAYERS_QUEUE = []


# Названия кораблей.
SHIPS = [
    'first_3',
    'second_3',
    'first_2',
    'second_2',
    'third_2',
    'first_1',
    'second_1',
]


# Строки поля.
ROW_LETTERS = ascii_uppercase[:8]

# Колонки поля.
COL_NUMBERS = digits[1: 9]


# Состояния.
STATES = dict()
