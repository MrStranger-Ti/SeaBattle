import sqlite3


def save_user(user, in_game):
    with sqlite3.connect('telebot.db') as conn:
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS `users`(
        `id` INTEGER NOT NULL PRIMARY KEY,
        `in_game` BOOLEAN
        )
        ''')

        cursor.execute('''
        INSERT INTO `users` (
            `id`,
            `in_game`
        )
        VALUES (
            ?,
            ?
        )
        ''', [user.id, in_game])
