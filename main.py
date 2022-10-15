import logging
import asyncio

from telebot.async_telebot import AsyncTeleBot

import utils.settings as settings
from utils.db import User, Payment, Notification

logging.basicConfig(
    filename='log.log',
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%m/%d/%Y %H:%M:%S',
    level=logging.DEBUG
)

bot = AsyncTeleBot(settings.API_KEY)


@bot.message_handler(commands=['help', 'start'])
async def start(message):
    logging.debug(f'User chose /start command')
    await bot.reply_to(message, 'Hello there!')


if __name__ == '__main__':
    asyncio.run(bot.infinity_polling(skip_pending=True))
