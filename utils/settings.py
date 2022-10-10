from contextlib import suppress


API_KEY = 'SOBAKA_BABAKA'

with suppress(ImportError):
    from utils.local_settings import *
