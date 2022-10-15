import logging
from contextlib import suppress

from peewee import SqliteDatabase


API_KEY = 'SOBAKA_BABAKA'

database = SqliteDatabase('default.db')

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%m/%d/%Y %H:%M:%S',
    level=logging.INFO
)

with suppress(ImportError):
    from utils.local_settings import *
