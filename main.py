import asyncio

from telebot.async_telebot import AsyncTeleBot
from telebot import types
from telebot.asyncio_filters import TextContainsFilter, StateFilter
from telebot.asyncio_storage import StateMemoryStorage
from telebot.asyncio_handler_backends import State, StatesGroup

import utils.settings as settings, logging
from utils.db import User, Payment, Notification

logger = logging.getLogger(__name__)

bot = AsyncTeleBot(settings.API_KEY, state_storage=StateMemoryStorage())
bot.add_custom_filter(TextContainsFilter())
bot.add_custom_filter(StateFilter(bot))


class MyStates(StatesGroup):
    change_name = State()


class Button:
    rename = 'Изменить имя'
    payments = 'Показать список сервисов'
    add_new_payment = 'Добавить новый сервис по оплате'
    change_payment = 'Изменить информацию'
    delete_payment = 'Удалить'
    notifications = 'Список уведомлений'
    add_new_notification = 'Добавить уведомление'
    change_notification = 'Изменить уведомление'
    delete_notification = 'Удалить'


@bot.message_handler(commands=['help', 'start'])
async def start(message):
    logger.debug(f'User {message.from_user.id} chose /start command')
    user = {
        'telegram_id': message.from_user.id,
    }
    if message.from_user.username:
        user.update({'username': message.from_user.username})
    User.get_or_create(**user)
    del user
    await bot.reply_to(message, 'Hello there!')
    await main_buttons(message.chat.id)


@bot.message_handler(text_contains=[Button.rename])
async def want_change_name(message):
    logger.debug(f'User wants change username')
    await bot.send_message(
        message.chat.id,
        'Ну-ка, и как ты хочешь называться теперь?',
        reply_markup=types.ReplyKeyboardRemove()
    )
    await bot.set_state(message.from_user.id, MyStates.change_name, message.chat.id)


@bot.message_handler(state=MyStates.change_name)
async def change_name(message):
    user = User.get_or_create(telegram_id=message.from_user.id)[0]
    logger.debug(f'User {user.username} change username to {message.text}')
    user.username = message.text
    user.save()
    await bot.send_message(
        message.chat.id,
        f'Отлично, в случае чего буду к тебе так обращаться!'
    )
    await bot.delete_state(message.from_user.id, message.chat.id)
    await main_buttons(message.chat.id)


async def main_buttons(chat_id: int) -> None:
    markup = types.ReplyKeyboardMarkup(row_width=2)
    user_rename = types.KeyboardButton(Button.rename)
    payments_list = types.KeyboardButton(Button.payments)
    markup.add(user_rename, payments_list)
    logger.debug(f'Show user main buttons')
    await bot.send_message(chat_id, 'Чего изволите?', reply_markup=markup)


if __name__ == '__main__':
    asyncio.run(bot.infinity_polling(skip_pending=True))
