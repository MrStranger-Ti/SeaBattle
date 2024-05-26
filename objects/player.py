import telebot.types

from string import ascii_letters

from objects.exeptions import PositionError

col_letters = ascii_letters[:10]


class Player:
    def __init__(self, user: telebot.types.User):
        self.object = user
        self.opponent: Player | None = None
        self.lost = False
        self.field = self.create_field()

    @staticmethod
    def create_field() -> list[list['Cell']]:
        return [
            [Cell(col_letters[row] + str(col + 1)) for col in range(10)]
            for row in range(10)
        ]

    @staticmethod
    def validate_position(position: str) -> bool:
        if len(position) in (2, 3) and position[0] in col_letters and position[1:].isdigit():
            return True
        return False

    def get_cell(self, position: str) -> 'Cell':
        if not self.validate_position(position):
            raise PositionError()

        row = col_letters.index(position[0])
        col = int(position[1:]) - 1
        return self.field[row][col]

    def set_ship(self, position: str) -> None:
        cell = self.get_cell(position)
        cell.is_ship = True

    def open_cell(self, position: str) -> bool:
        cell = self.get_cell(position)
        cell.opened = True
        return cell.is_ship

    def open_opponent_cell(self, position: str) -> bool:
        if self.opponent:
            return self.opponent.open_cell(position)
        return False


class Cell:
    def __init__(self, position: str):
        self.position: str = position
        self.opened: bool = False
        self.is_ship: bool = False
