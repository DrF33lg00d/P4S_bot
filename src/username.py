from utils.db import User


def create_or_update_user(telegram_id: int, username: str):
    user = {
        'telegram_id': telegram_id,
    }
    if username:
        user.update({'username': username})
    User.get_or_create(**user)
    del user


def change_username(telegram_id: int, new_username: str):
    user = User.get_or_create(telegram_id=telegram_id)[0]
    user.username = new_username
    user.save()
    del user
