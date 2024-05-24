import os
import telebot
import dotenv
import logging

logging.basicConfig(level='INFO')

logger = logging.getLogger(__name__)

dotenv.load_dotenv()

TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, 'Привет!')


@bot.message_handler()
def echo(message):
    bot.reply_to(message, message.text)


if __name__ == '__main__':
    logger.info('Бот запущен!')
    bot.infinity_polling()
