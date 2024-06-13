from string import ascii_uppercase

# Очередь игроков.
PLAYERS_QUEUE = []

# Названия кораблей.
ships: list[str] = [
    'first_3',
    'second_3',
    'first_2',
    'second_2',
    'first_1',
    'second_1',
    'third_1',
]

# Строки поля
row_letters = ascii_uppercase[:8]

# Колонки поля
col_numbers = [str(num) for num in range(1, 9)]
