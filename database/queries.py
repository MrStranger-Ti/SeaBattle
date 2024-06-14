import sqlite3

from settings import DATABASE_PATH


def create_tables() -> None:
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS `rating`(
            `id` INT PRIMARY KEY,
            `value` INT
        )
        ''')


def update_or_add_rating(user_id: int, rating: int) -> None:
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT *
        FROM `rating`
        WHERE `id` = ?
        ''', (user_id,))

        if cursor.fetchone():
            cursor.execute('''
            UPDATE `rating` SET
                `value` = `value` + ?
            WHERE `id` == ?
            ''', (rating, user_id))

        else:
            cursor.execute('''
            INSERT INTO `rating`(
                `id`,
                `value`
            )
            VALUES (
                ?,
                ?
            )
            ''', (user_id, rating))
