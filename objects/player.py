import re

import telebot.types

from string import ascii_lowercase

from objects.exeptions import PositionError, CellOpenedError

row_letters = ascii_lowercase[:10]
col_numbers = [str(num) for num in range(1, 11)]


class Player:
    """
    Сущность игрока.

    Имеет свое поле и управляет им.
    Также он может попросить открыть ячейку другого игрока.
    """
    def __init__(self, user: telebot.types.User):
        self.object = user
        self.opponent: Player | None = None
        self.lost = False
        self.field = self.create_field()

    @staticmethod
    def create_field() -> list[list['Cell']]:
        """
        Генерация поля.

        Поле будет являться вложенным списком. Размер 10X10.
        """
        return [
            [Cell(row_letters[row] + str(col + 1)) for col in range(10)]
            for row in range(10)
        ]

    @staticmethod
    def validate_position(position: str) -> bool:
        """
        Валидация позиции ячейки, который передал игрок.

        Для валидации используется регулярное выражение.

        Примеры:

        e8 - верно
        d10 - верно
        d11 - неверно
        x1 - неверно
        f0 - неверно
        """
        if not re.fullmatch(r'[a-j][1-9]0?', position):
            return False

        return True

    def get_cell(self, position: str) -> 'Cell':
        """
        Получение ячейки.
        """
        # Если валидация не проша, то возбуждаем ошибку PositionError.
        if not self.validate_position(position):
            raise PositionError()

        # Получаем индексы из позиции, а затем получаем ячейку по этим индексам.
        row = row_letters.index(position[0])
        col = int(position[1:]) - 1
        return self.field[row][col]

    def set_ship(self, position: str) -> None:
        """
        Установка корабля по переданной позиции.
        """
        cell = self.get_cell(position)
        cell.is_ship = True

    def open_cell(self, position: str) -> bool:
        """
        Открытие ячейки.

        Возвращается True, если удалось открыть ячейку игрока, False в противном случае.
        """
        cell = self.get_cell(position)

        # Если ячейка уже открыта, то возбуждаем ошибку CellOpenedError
        if cell.opened:
            raise CellOpenedError()

        cell.opened = True
        return cell.is_ship

    def open_opponent_cell(self, position: str) -> bool:
        """
        Открытие ячейки соперника.

        Возвращается True, если удалось открыть ячейку соперника, False в противном случае.
        """
        # Проверяем, что у игрока установлен соперник.
        if self.opponent:
            return self.opponent.open_cell(position)
        return False


class Cell:
    """
    Сущность ячейки.

    Attributes:
        position (str): позиция ячейки
        opened (bool): открыта ли ячейка
        is_ship (bool): стоит ли корабль на ячейке
    """
    def __init__(self, position: str):
        self.position: str = position
        self.opened: bool = False
        self.is_ship: bool = False
