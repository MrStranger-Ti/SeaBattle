import io
import re
from typing import Optional

import PIL

from PIL import ImageDraw, Image, ImageFont
from telebot.types import User

from settings import SHIPS, ROW_LETTERS, COL_NUMBERS
from objects.exceptions import PositionError, CellOpenedError, ShipNearbyError


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
        field_img (Image.Image): нарисованное пустое поле с помощью Pillow
        ships (dict[int: list[Cell]): ключ - название корабля; значение - ячейки этого корабля
    """
    def __init__(self, user: User):
        self.object: User = user
        self.opponent: Optional[Player] = None
        self.ready: Optional[bool] = None
        self.lost: bool = False
        self.field: list[list[Cell]] = self.create_field()
        self.field_img: Image.Image = self.draw_empty_field()
        self.ships: dict[str: list['Cell']] = {
            name: []
            for name in SHIPS
        }

    def __str__(self):
        return self.object.username or self.object.first_name

    @staticmethod
    def create_field() -> list[list['Cell']]:
        """
        Генерация поля.

        Поле является вложенным списком. Размер 8X8.

        :return вложенный список
        """
        return [
            [Cell(ROW_LETTERS[row] + str(col + 1)) for col in range(8)]
            for row in range(8)
        ]

    @staticmethod
    def draw_empty_field() -> Image.Image:
        """
        Отрисовка пустого поля.

        :return объект изображения
        """
        # Создание изображения.
        img = Image.new('RGBA', (280, 280), 'white')

        # Создание объекта для рисования
        pencil = ImageDraw.Draw(img)

        # Отступы и шрифт:
        # gap - расстояние между символами;
        # dist_edge_to_symbols - расстояние от края до символов;
        # dist_edge_to_first_symbol - расстояние от края до первого символа;
        # font - шрифт.
        gap = 30.5
        dist_edge_to_symbols = 5
        dist_edge_to_first_symbol = 29
        font = PIL.ImageFont.truetype('arial', size=18)

        # Отрисовка букв и цифр.
        for num, letter in enumerate(ROW_LETTERS):
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

        # Параметры для отрисовки поля:
        # width - ширина поля;
        # height - высота поля;
        # x0, y0 - координаты верхней левой точки поля;
        # x1, y1 - координаты нижней правой точки поля;
        # cell_size - размер одной ячейки.
        width = 240
        height = 240
        x0 = 20
        y0 = 25
        x1 = width + x0
        y1 = height + y0
        cell_size = width // 8

        # Отрисовка квадрата.
        pencil.rectangle((x0, y0, x1, y1), outline='black')

        # Отрисовка горизонтальных и вертикальных линий.
        for num in range(len(ROW_LETTERS) - 1):
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
        """
        Отрисовка ячеек поля игрока.

        :param opponent: нужно ли рисовать поле как вражеское
        :return двоичный поток
        """
        # Рисовать ли поле как вражеское.
        if opponent:
            field = self.opponent.field
        else:
            field = self.field

        # Копируем изображение
        copied_field = self.field_img.copy()

        # Создаем объект для рисования
        pencil = ImageDraw.Draw(copied_field)

        # x_rectangle, y_rectangle - координаты верхнего левого пикселя поля.
        x_rectangle = 20
        y_rectangle = 25

        # Отрисовка ячеек.
        for row_num, row in enumerate(field):
            for col_num, cell in enumerate(row):
                # cell_size - размер ячейки;
                # cell_x, cell_y - координаты до верхнего левого пикселя ячейки.
                cell_size = 30
                cell_x = x_rectangle + col_num * cell_size
                cell_y = y_rectangle + row_num * cell_size
                rectangle_coords = [
                    (cell_x + 5, cell_y + 5),
                    (cell_x + (cell_size - 5), cell_y + (cell_size - 5)),
                ]

                # Определяем какого цвета должна быть ячейка.
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
                        color = 'yellow'

                    elif cell.opened:
                        color = 'blue'

                # Если color = None, то ячейка остается пустой (без цвета)
                if color:
                    pencil.rectangle(rectangle_coords, fill=color, width=2)

        return self.get_io_field_image(copied_field)

    @staticmethod
    def get_io_field_image(img: Image.Image) -> io.BytesIO:
        """
        Получение изображение поля в виде двоичного потока.

        :param img: изображение поля
        """
        bio = io.BytesIO()
        bio.name = 'field.jpeg'
        img.save(bio, 'PNG')
        bio.seek(0)
        return bio

    def get_cell(self, position: str) -> 'Cell':
        """
        Получение ячейки.

        :param position: позиция ячейки
        """
        # Если валидация не прошла, то возбуждаем ошибку PositionError.
        if not self.validate_position(position):
            raise PositionError()

        # Получаем индексы из позиции, а затем получаем ячейку по этим индексам.
        row = ROW_LETTERS.index(position[0].upper())
        col = int(position[1:]) - 1
        return self.field[row][col]

    def set_ship(self, position: str, name: str, direction: Optional[str] = None) -> None:
        """
        Установка корабля по переданной позиции и направлению.

        :param position: позиция ячейки
        :param name: название корабля
        :param direction: в какую сторону разместить остальные части корабля
        """
        # Если направление неверное, то возбуждаем ошибку.
        if direction and direction.lower() not in ('top', 'right', 'bottom', 'left'):
            raise ValueError('Передано неверное направление.')

        # Если направление передано, то меняем ему регистр на нижний.
        if direction:
            direction = direction.lower()

        # ship_size - количество ячеек у корабля.
        ship_size = int(name[-1])

        # Получаем первую ячейку будущего корабля и сохраняем ее.
        cell = self.get_cell(position)
        cells = [cell]

        # Определяем остальные ячейки в переданном направлении.
        # Если какая-то ячейка в переданном направлении неверна, то возбуждаем ошибку PositionError.
        cur_position = cell.position
        for _ in range(ship_size - 1):
            ind_cur_row = ROW_LETTERS.index(cur_position[0])
            ind_cur_col = COL_NUMBERS.index(cur_position[1:])

            if direction == 'top':
                ind_next_row = ind_cur_row - 1
                if ind_next_row < 0:
                    raise PositionError()

                next_position = ROW_LETTERS[ind_next_row] + cur_position[1:]

            elif direction == 'right':
                ind_next_col = ind_cur_col + 1
                if ind_next_col > len(COL_NUMBERS) - 1:
                    raise PositionError()

                next_position = cur_position[0] + COL_NUMBERS[ind_next_col]

            elif direction == 'bottom':
                ind_next_row = ind_cur_row + 1
                if ind_next_row > len(ROW_LETTERS) - 1:
                    raise PositionError()

                next_position = ROW_LETTERS[ind_next_row] + cur_position[1:]

            elif direction == 'left':
                ind_next_col = ind_cur_col - 1
                if ind_next_col < 0:
                    raise PositionError()

                next_position = cur_position[0] + COL_NUMBERS[ind_next_col]

            next_cell = self.get_cell(next_position)
            cells.append(next_cell)

            cur_position = next_position

        # Если поблизости с полученными ячейками есть корабли, то возбуждаем ошибку ShipNearbyError.
        for cell in cells:
            if not self.valid_cell(cell):
                raise ShipNearbyError()

        # Устанавливаем корабль на полученные ячейки и сохраняем эти ячейки.
        for cell in cells:
            cell.is_ship = True
            self.ships.get(name).append(cell)

    def open_cell(self, position: str) -> bool:
        """
        Открытие ячейки.

        Возвращается True, если удалось открыть ячейку игрока, False в противном случае.

        :param position: позиция ячейки, которую необходимо открыть
        :return стоял ли корабль на ячейке
        """
        cell = self.get_cell(position)

        # Если ячейка уже открыта, то возбуждаем ошибку CellOpenedError.
        if cell.opened:
            raise CellOpenedError()

        # Открытие переданной ячейки и лишних ячеек неподалеку.
        cell.opened = True
        self.open_unnecessary_cells(cell)

        # Если у игрока не осталось кораблей, то меняем self.lost на True.
        if self.is_loser():
            self.lost = True

        return cell.is_ship

    def open_unnecessary_cells(self, cell: 'Cell') -> None:
        """
        Открытие лишних клеток.

        :param cell: ячейка
        """
        # Если переданная ячейка не является кораблем, то ничего не делаем.
        if not cell.is_ship:
            return

        # Определяем открыт ли уже корабль или нет.
        ship_opened = self.ship_opened(cell)

        # Если корабль открыт, то можно открыть все ячейки рядом.
        # Если же корабль не открыт, то открываем только клетки по диагонали.
        if ship_opened:
            ship_cells = self.get_ship_cells(cell)
            nearby_ship_cells = set()
            for cell in ship_cells:
                nearby_cells = self.get_cells_nearby(cell)
                nearby_ship_cells.update(nearby_cells)

            for nearby_ship_cell in nearby_ship_cells:
                if nearby_ship_cell:
                    nearby_ship_cell.opened = True
        else:
            cells_nearby = self.get_cells_nearby(cell)
            for num, nearby_cell in enumerate(cells_nearby):
                if nearby_cell and (num % 2 == 0 or ship_opened):
                    nearby_cell.opened = True

    def open_opponent_cell(self, position: str) -> bool:
        """
        Открытие ячейки соперника.

        Возвращается True, если удалось открыть ячейку соперника, False в противном случае.

        :param position: позиция ячейки, которую необходимо открыть
        :return bool
        """
        # Проверяем, что у игрока установлен соперник.
        if self.opponent:
            return self.opponent.open_cell(position)
        return False

    def get_ship_cells(self, cell: 'Cell') -> list['Cell']:
        """
        Получение всех ячеек корабля по переданной ячейки.

        Если передана ячейка, которая не является кораблем, то возвращается пустой список.

        :param cell: ячейка, по которой определяется корабль
        :return: список из ячеек
        """
        for ship_cells in self.ships.values():
            if cell in ship_cells:
                return ship_cells

        return list()

    def get_cells_nearby(self, cell: 'Cell') -> list[Optional['Cell']]:
        """
        Получение всех ячеек, которые находятся рядом с переданной.

        :param cell: ячейка, по которой будут находиться все ближайшие ячейки
        :return: список ближайших ячеек
        """
        # Получение индексов переданной ячейки.
        ind_row = ROW_LETTERS.index(cell.position[0])
        ind_col = COL_NUMBERS.index(cell.position[1:])

        # Получение индексов всех ближних ячеек.
        indices = [
            (ind_row - 1, ind_col - 1),
            (ind_row - 1, ind_col),
            (ind_row - 1, ind_col + 1),
            (ind_row, ind_col + 1),
            (ind_row + 1, ind_col + 1),
            (ind_row + 1, ind_col),
            (ind_row + 1, ind_col - 1),
            (ind_row, ind_col - 1),
        ]

        # Если ячейка неверна, то сохраняем None в списке, иначе саму ячейку.
        cells_nearby = []
        for ind_row, ind_col in indices:
            if 0 <= ind_row <= len(ROW_LETTERS) - 1 and 0 <= ind_col <= len(COL_NUMBERS) - 1:
                cell = self.field[ind_row][ind_col]
                cells_nearby.append(cell)
            else:
                cells_nearby.append(None)

        return cells_nearby

    def ship_opened(self, cell: 'Cell') -> bool:
        """
        Открыт ли полностью корабль.

        :param cell: ячейка, по которой будет определяться ячейка корабля
        :return: bool
        """
        for cells in self.ships.values():
            if cell in cells and all(ship_cell.is_ship and ship_cell.opened for ship_cell in cells):
                return True

        return False

    def all_ships_on_field(self) -> bool:
        """
        Все ли корабли установлены.

        :return: bool
        """
        for name, cells in self.ships.items():
            if len(cells) != int(name[-1]):
                return False

        return True

    @staticmethod
    def validate_position(position: str) -> bool:
        """
        Валидация позиции ячейки.

        Для валидации используется регулярное выражение.

        :param position: позиция ячейки
        """
        if not re.fullmatch(r'[a-hA-H][1-8]', position):
            return False

        return True

    def valid_cell(self, cell: 'Cell') -> bool:
        """
        Можно ли ставить на переданную ячейку корабль.

        :param cell: ячейка
        :return: bool
        """
        # Если на ячейке стоит кораблем, то возвращаем False.
        if cell.is_ship:
            return False

        # Если на ближайших ячейках стоит корабль, то возвращаем False.
        cells_nearby = self.get_cells_nearby(cell)
        for cell in cells_nearby:
            if cell and cell.is_ship:
                return False

        return True

    def is_loser(self) -> bool:
        """
        Проиграл ли игрок.

        Если все ячейки у кораблей открыты, то возвращаем True, иначе False.

        :return: bool
        """
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
