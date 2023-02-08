import logging
from contextlib import suppress

from peewee import SqliteDatabase
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from src.states import MainStates, NotificationStates, PaymentStates


API_KEY = 'SOBAKA_BABAKA'

database = SqliteDatabase('default.db')

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%m/%d/%Y %H:%M:%S',
    level=logging.INFO
)

with suppress(ImportError):
    from utils.local_settings import *


bot = Bot(API_KEY)
storage = MemoryStorage()

dp = Dispatcher(bot, storage=storage)
