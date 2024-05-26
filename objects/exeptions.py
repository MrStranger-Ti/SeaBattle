class PositionError(Exception):
    def __str__(self):
        return 'Передана неверная позиция для поля'
