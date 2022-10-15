import asyncio

from telebot.async_telebot import AsyncTeleBot

import utils.settings as settings, logging
from utils.db import User, Payment, Notification

logger = logging.getLogger(__name__)

bot = AsyncTeleBot(settings.API_KEY)


@bot.message_handler(commands=['help', 'start'])
async def start(message):
    logger.debug(f'User chose /start command')
    await bot.reply_to(message, 'Hello there!')


if __name__ == '__main__':
    asyncio.run(bot.infinity_polling(skip_pending=True))
