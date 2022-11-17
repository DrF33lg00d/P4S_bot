from telebot.asyncio_handler_backends import State, StatesGroup

from utils.db import User


class ChangeNameStates(StatesGroup):
    change_name = State()


def create_or_update_user(telegram_id: int, username: str):
    user = {
        'telegram_id': telegram_id,
    }
    if username:
        user.update({'username': username})
    User.get_or_create(**user)
    del user
