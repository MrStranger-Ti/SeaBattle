import re

from telebot.types import User

from string import ascii_lowercase

from objects.exceptions import PositionError, CellOpenedError, ShipNearbyError

row_letters = ascii_lowercase[:10]
col_numbers = [str(num) for num in range(1, 11)]


class Player:
    """
    Сущность игрока.

    Имеет свое поле и управляет им.
    Также он может попросить открыть ячейку другого игрока.

    Attributes:
        object (User): объект пользователя из библиотеки telebot
        opponent (Player): соперник игрока
        ready (bool): готов ли игрок к игре
        lost (bool): проиграл ли игрок или нет
        field (list[list[Cell]]): поле игрока
        ships (dict[int: int]): какие корабли остались и сколько
    """
    def __init__(self, user: User):
        self.object: User = user
        self.opponent: Player | None = None
        self.ready: bool | None = None
        self.lost: bool = False
        self.field: list[list[Cell]] = self.create_field()
        self.ships: dict[int: int] = {}

    def all_ships_on_field(self) -> bool:
        valid_ships_count = (1, 2, 3, 4)
        if tuple(self.ships.values()) == valid_ships_count:
            return True
        return False

    @staticmethod
    def create_field() -> list[list['Cell']]:
        """
        Генерация поля.

        Поле является вложенным списком. Размер 10X10.
        """
        return [
            [Cell(row_letters[row] + str(col + 1)) for col in range(10)]
            for row in range(10)
        ]

    @staticmethod
    def validate_position(position: str) -> bool:
        """
        Валидация позиции ячейки.

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
        # Если валидация не прошла, то возбуждаем ошибку PositionError.
        if not self.validate_position(position):
            raise PositionError()

        # Получаем индексы из позиции, а затем получаем ячейку по этим индексам.
        row = row_letters.index(position[0])
        col = int(position[1:]) - 1
        return self.field[row][col]

    def set_ship(self, position: str, size: int, direction: str) -> None:
        """
        Установка корабля по переданной позиции.
        """
        if direction not in ('top', 'right', 'bottom', 'left'):
            raise ValueError('Передано неверное направление.')

        cell = self.get_cell(position)

        cells = [cell]
        cur_position = cell.position
        for _ in range(size - 1):
            ind_cur_row = row_letters.index(cur_position[0])
            ind_cur_col = col_numbers.index(cur_position[1:])

            if direction == 'top':
                ind_next_row = ind_cur_row - 1
                if ind_next_row < 0:
                    raise PositionError()

                next_position = row_letters[ind_next_row] + cur_position[1:]

            elif direction == 'right':
                ind_next_col = ind_cur_col + 1
                if ind_next_col > len(col_numbers) - 1:
                    raise PositionError()

                next_position = cur_position[0] + col_numbers[ind_next_col]

            elif direction == 'bottom':
                ind_next_row = ind_cur_row + 1
                if ind_next_row > len(row_letters) - 1:
                    raise PositionError()

                next_position = row_letters[ind_next_row] + cur_position[1:]

            elif direction == 'left':
                ind_next_col = ind_cur_col - 1
                if ind_next_col < 0:
                    raise PositionError()

                next_position = cur_position[0] + col_numbers[ind_next_col]

            next_cell = self.get_cell(next_position)
            cells.append(next_cell)

            cur_position = next_position

        for cell in cells:
            if not self.valid_cell(cell):
                raise ShipNearbyError()

        for cell in cells:
            cell.is_ship = True

        self.ships[size] = self.ships.get(size, 0) + 1

    def valid_cell(self, cell: 'Cell') -> bool:
        if cell.is_ship:
            return False

        ind_row = row_letters.index(cell.position[0])
        ind_col = col_numbers.index(cell.position[1:])
        indices = [
            (ind_row - 1, ind_col),
            (ind_row - 1, ind_col + 1),
            (ind_row, ind_col + 1),
            (ind_row + 1, ind_col + 1),
            (ind_row + 1, ind_col),
            (ind_row + 1, ind_col - 1),
            (ind_row, ind_col - 1),
            (ind_row - 1, ind_col - 1),
        ]

        cells_nearby = []
        for ind_row, ind_col in indices:
            try:
                cell = self.field[ind_row][ind_col]
            except IndexError:
                continue

            cells_nearby.append(cell)

        for cell in cells_nearby:
            if cell.is_ship:
                return False

        return True

    def open_cell(self, position: str) -> bool:
        """
        Открытие ячейки.

        Возвращается True, если удалось открыть ячейку игрока, False в противном случае.
        """
        cell = self.get_cell(position)

        # Если ячейка уже открыта, то возбуждаем ошибку CellOpenedError.
        if cell.opened:
            raise CellOpenedError()

        cell.opened = True

        # Если у игрока не осталось кораблей, то меняем self.lost на True.
        ...

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
