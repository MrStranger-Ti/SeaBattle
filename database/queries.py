import sqlite3

from telebot.types import User

from settings import DATABASE_PATH


def create_tables() -> None:
    """
    Создание всех необходимых таблиц, если они не созданы.
    """
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS `users`(
            `id` INT PRIMARY KEY,
            `username` CHAR(256),
            `rating` INT
        )
        ''')


def update_or_add_rating(user: User, rating: int) -> None:
    """
    Обновление или добавление рейтинга.

    :param user: пользователь Telegram
    :param rating: рейтинг пользователя
    """
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT *
        FROM `users`
        WHERE `id` = ?
        ''', (user.id,))

        if cursor.fetchone():
            cursor.execute('''
            UPDATE `users` SET
                `rating` = `rating` + ?
            WHERE `id` == ?
            ''', (rating, user.id))

        else:
            cursor.execute('''
            INSERT INTO `users`(
                `id`,
                `username`,
                `rating`
            )
            VALUES (
                ?,
                ?,
                ?
            )
            ''', (user.id, user.username or user.first_name, rating))


def get_users() -> list[tuple[int, int, int]]:
    """
    Получение рейтинга всех пользователей.

    :return: рейтинг пользователей

    Возвращает id пользователей и их рейтинг в виде списка с кортежами.
    Например, [(1, Sam, 2), (2, dsdaa228, 8), (3, fhie343d, 3)].
    """
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute('''
        SELECT *
        FROM `users`
        ORDER BY `rating` DESC
        ''')

        rating = cursor.fetchall()

    return rating
