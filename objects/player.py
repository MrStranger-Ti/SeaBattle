import io
import re

import PIL

from string import ascii_uppercase

from PIL import ImageDraw, Image, ImageFont
from telebot.types import User

from objects.exceptions import PositionError, CellOpenedError, ShipNearbyError

row_letters = ascii_uppercase[:6]
col_numbers = [str(num) for num in range(1, 7)]


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
        field_img (Image.Image): Нарисованное пустое поле с помощью Pillow
        ships (dict[int: int]): какие корабли остались и сколько
    """
    def __init__(self, user: User):
        self.object: User = user
        self.opponent: Player | None = None
        self.ready: bool | None = None
        self.lost: bool = False
        self.field: list[list[Cell]] = self.create_field()
        self.field_img: Image.Image = self.draw_empty_field()
        self.ships: dict[int: int] = {}

    @staticmethod
    def create_field() -> list[list['Cell']]:
        """
        Генерация поля.

        Поле является вложенным списком. Размер 10X10.
        """
        return [
            [Cell(row_letters[row] + str(col + 1)) for col in range(6)]
            for row in range(6)
        ]

    @staticmethod
    def draw_empty_field() -> Image.Image:
        img = Image.new('RGBA', (220, 220), 'white')
        pencil = ImageDraw.Draw(img)

        gap = 30.5
        dist_edge_to_symbols = 5
        dist_edge_to_first_symbol = 29
        font = PIL.ImageFont.truetype('arial', size=18)

        for num, letter in enumerate(row_letters):
            color = 'black'

            pencil.text(
                xy=(dist_edge_to_symbols, dist_edge_to_first_symbol + (num * gap)),
                text=letter,
                font=font,
                fill=color,
            )
            pencil.text(
                xy=(dist_edge_to_first_symbol + (num * gap), dist_edge_to_symbols),
                text=str(num + 1),
                font=font,
                fill=color,
            )

        width = 180
        height = 180
        x0 = 20
        y0 = 25
        x1 = width + x0
        y1 = height + y0
        pencil.rectangle((x0, y0, x1, y1), outline='black')
        cell_size = width // 6
        for num in range(len(row_letters) - 1):
            num += 1
            horizontal_lines_coords = [
                (x0, y0 + (num * cell_size)),
                (x1, y0 + (num * cell_size)),
            ]
            vertical_lines_coords = [
                (x0 + (num * cell_size), y0),
                (x0 + (num * cell_size), y1),
            ]

            pencil.line(horizontal_lines_coords, fill='black', width=1)
            pencil.line(vertical_lines_coords, fill='black', width=1)

        return img

    def draw_player_field(self, opponent: bool = False) -> io.BytesIO:
        if opponent:
            field = self.opponent.field
        else:
            field = self.field

        copied_field = self.field_img.copy()
        pencil = ImageDraw.Draw(copied_field)

        x_rectangle = 20
        y_rectangle = 25
        for row_num, row in enumerate(field):
            for col_num, cell in enumerate(row):
                cell_size = 30
                cell_x = x_rectangle + col_num * cell_size
                cell_y = y_rectangle + row_num * cell_size
                rectangle_coords = [
                    (cell_x + 5, cell_y + 5),
                    (cell_x + (cell_size - 5), cell_y + (cell_size - 5)),
                ]

                color = None
                if opponent:
                    if cell.opened and cell.is_ship:
                        color = 'green'

                    elif not cell.opened:
                        color = 'black'
                else:
                    if cell.opened and cell.is_ship:
                        color = 'red'

                    elif cell.is_ship:
                        color = 'blue'

                    elif cell.opened:
                        color = 'yellow'

                if color:
                    pencil.rectangle(rectangle_coords, fill=color, width=2)

        return self.get_io_field_image(copied_field)

    @staticmethod
    def get_io_field_image(img: Image.Image) -> io.BytesIO:
        bio = io.BytesIO()
        bio.name = 'field.jpeg'
        img.save(bio, 'PNG')
        bio.seek(0)
        return bio

    def get_cell(self, position: str) -> 'Cell':
        """
        Получение ячейки.
        """
        # Если валидация не прошла, то возбуждаем ошибку PositionError.
        if not self.validate_position(position):
            raise PositionError()

        # Получаем индексы из позиции, а затем получаем ячейку по этим индексам.
        row = row_letters.index(position[0].upper())
        col = int(position[1:]) - 1
        return self.field[row][col]

    def set_ship(self, position: str, size: int, direction: str | None = None) -> None:
        """
        Установка корабля по переданной позиции.
        """
        if direction and direction.lower() not in ('top', 'right', 'bottom', 'left'):
            raise ValueError('Передано неверное направление.')

        if direction:
            direction = direction.lower()

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
        if self.is_loser():
            self.lost = True

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

    def all_ships_on_field(self) -> bool:
        valid_ships_count = (1, 1, 2)
        if tuple(self.ships.values()) == valid_ships_count:
            return True
        return False

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
        if not re.fullmatch(r'[a-fA-F][1-6]', position):
            return False

        return True

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
            if 0 <= ind_row <= len(row_letters) - 1 and 0 <= ind_col <= len(col_numbers) - 1:
                cell = self.field[ind_row][ind_col]
                cells_nearby.append(cell)

        for cell in cells_nearby:
            if cell.is_ship:
                return False

        return True

    def is_loser(self):
        for row in self.field:
            for cell in row:
                if cell.is_ship and not cell.opened:
                    return False

        return True


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
