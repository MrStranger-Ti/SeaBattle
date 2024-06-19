from telebot import types
from telebot.types import ReplyKeyboardMarkup

def keyboard_start() -> ReplyKeyboardMarkup:
    """
    Создание клавиатуры для команды /start.

    :return: кнопки
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("👥Подбор игроков👥")
    btn2 = types.KeyboardButton("🏆Рейтинг🏆")
    btn3 = types.KeyboardButton("📕Информация📕")
    markup.row(btn1, btn2)
    markup.row(btn3)

    return markup

def keyboard_play() -> ReplyKeyboardMarkup:
    """
    Создание клавиатуры для команды /play.

    :return: кнопки
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Покинуть очередь или игру")
    markup.add(btn1)

    return markup