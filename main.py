import os
import telebot
import dotenv

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
    bot.infinity_polling()
