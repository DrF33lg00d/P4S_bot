import logging
from contextlib import suppress

from peewee import SqliteDatabase
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_filters import TextContainsFilter, StateFilter, IsReplyFilter, IsDigitFilter
from telebot.asyncio_storage import StateMemoryStorage
from telebot.asyncio_handler_backends import State, StatesGroup


API_KEY = 'SOBAKA_BABAKA'

database = SqliteDatabase('default.db')

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%m/%d/%Y %H:%M:%S',
    level=logging.INFO
)

with suppress(ImportError):
    from utils.local_settings import *


bot = AsyncTeleBot(API_KEY, state_storage=StateMemoryStorage())
bot.add_custom_filter(TextContainsFilter())
bot.add_custom_filter(IsReplyFilter())
bot.add_custom_filter(IsDigitFilter())
bot.add_custom_filter(StateFilter(bot))


class MainStates(StatesGroup):
    main_menu = State()
    change_name = State()
