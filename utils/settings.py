import logging
from contextlib import suppress
from collections import defaultdict

from peewee import SqliteDatabase
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage


API_KEY = 'SOBAKA_BABAKA'
PAYMENTS = defaultdict(dict)
CACHE_CLEAR_TIMER = 300

database = SqliteDatabase('default.db')

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%m/%d/%Y %H:%M:%S',
    level=logging.INFO
)


def get_day_word(day: int) -> str:
    if day % 10 == 1:
        return 'день'
    elif (2 <= day % 10 <= 4) and (10 > day % 100 or day % 100 > 20):
        return 'дня'
    else:
        return 'дней'


bot = Bot(API_KEY)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


with suppress(ImportError):
    from utils.local_settings import *
