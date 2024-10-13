# Sea Battle

Морской бой в Телеграм, в который можно играть вчетвером сразу. Также одновременно может быть несколько игровых сессий.

## Содержание

- [Технологии](#технологии)
- [Запуск](#запуск)
- [Env файл](#env-файл)
- [команды](#команды)
- [разработчик](#разработчик)

## Технологии

- [Python](https://www.python.org/)
- [pyTelegramBotAPI](https://pypi.org/project/pyTelegramBotAPI/)
- [pillow](https://pypi.org/project/pillow/)
- [sqlite3](https://www.sqlite.org/)

## Запуск

- Получите токен у [BotFather](https://t.me/BotFather)
- Создайте файл `.env`
- Установите переменную **TOKEN** в `.env`
- Запустите бота:
  ```
  python main.py
  ```

## Env файл

**TOKEN** - специальный токен бота, который выдает [BotFather](https://t.me/BotFather)

**TOTAL_SESSION_PLAYERS** - количество игроков в одной сессии

По умолчанию: 4

**CLEAR_BUFFER_TIME** - сколько сообщения бота будут оставаться в чате (сек.).

По умолчанию: 24 мин.

## Команды

**/start** - запуск бота и приветствие

**/info** - информация о боте

**/rating** - посмотреть рейтинг игроков (первые 10 и свой)

**/play** - начать подбор игроков

**/leave** - покинуть игру или подбор игроков

## Разработчик

- Андрей Сорокожердьев
  - [Telegram](https://t.me/MrStrangerTi)
  - asorokozherdyev@gmail.com