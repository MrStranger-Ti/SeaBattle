import os.path
from string import ascii_uppercase

# Основные настройки.
BASE_DIR = os.path.dirname(__file__)
DATABASE_PATH = os.path.join(BASE_DIR, 'database.db')

# Очередь игроков.
PLAYERS_QUEUE = []

# Названия кораблей.
ships: list[str] = [
    'first_3',
    'second_3',
    'third_3',
    'first_2',
    'second_2',
    'third_2',
    'first_1',
]

# Строки поля.
row_letters = ascii_uppercase[:8]

# Колонки поля.
col_numbers = [str(num) for num in range(1, 9)]
