class PositionError(Exception):
    """
    Ошибка, которая возбуждается, если игрок передал неправильную позицию.
    """
    def __str__(self):
        return 'Передана неверная позиция для поля.'


class ShipNearbyError(Exception):
    def __str__(self):
        return 'Рядом с ячейкой стоит другой корабль.'


class CellOpenedError(Exception):
    """
    Ошибка, которая возбуждается, если игрок указал на уже открытую ячейку.
    """
    def __str__(self):
        return 'Ячейка уже открыта.'
