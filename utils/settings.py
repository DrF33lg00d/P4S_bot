from contextlib import suppress

from peewee import SqliteDatabase


API_KEY = 'SOBAKA_BABAKA'

database = SqliteDatabase('default.db')


with suppress(ImportError):
    from utils.local_settings import *
