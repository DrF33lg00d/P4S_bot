import asyncio
from datetime import datetime

from telebot.async_telebot import AsyncTeleBot
from telebot import types
from telebot.asyncio_filters import TextContainsFilter, StateFilter, IsReplyFilter
from telebot.asyncio_storage import StateMemoryStorage

from utils import settings
from src.buttons import get_main_markup, get_payments_markup, Button
from src.username import ChangeNameStates, create_or_update_user, change_username
from src.payments import PaymentStates, get_payment_list, add_payment, delete_payment
from utils.db import User, Payment, Notification

logger = settings.logging.getLogger(__name__)

bot = AsyncTeleBot(settings.API_KEY, state_storage=StateMemoryStorage())
bot.add_custom_filter(TextContainsFilter())
bot.add_custom_filter(IsReplyFilter())
bot.add_custom_filter(StateFilter(bot))


def run():
    asyncio.run(bot.infinity_polling(skip_pending=True))


@bot.message_handler(commands=['help', 'start'])
async def start(message):
    logger.debug(f'User {message.from_user.id} chose /start command')
    create_or_update_user(message.from_user.id, message.from_user.username)
    await bot.reply_to(message, 'Hello there!')
    await main_buttons(message.chat.id)


async def main_buttons(chat_id: int) -> None:
    logger.debug(f'Show user main buttons')
    await bot.send_message(chat_id, 'Чего изволите?', reply_markup=get_main_markup())


@bot.message_handler(text_contains=[Button.rename])
async def pre_change_name(message):
    logger.debug(f'User wants change username')
    await bot.send_message(
        message.chat.id,
        'Ну-ка, и как ты хочешь называться теперь?',
        reply_markup=types.ReplyKeyboardRemove()
    )
    await bot.set_state(message.from_user.id, ChangeNameStates.change_name, message.chat.id)


@bot.message_handler(state=ChangeNameStates.change_name)
async def change_name(message):
    logger.debug(f'User change username to {message.text}')
    change_username(message.from_user.id, message.text)
    await bot.send_message(
        message.chat.id,
        f'Отлично, в случае чего буду к тебе так обращаться!'
    )
    await bot.delete_state(message.from_user.id, message.chat.id)
    await main_buttons(message.chat.id)


@bot.message_handler(text_contains=[Button.payments])
async def payments_list(message):
    logger.debug(f'User select payments list')
    payments = [
        f'{count + 1}.\t{payment.description}'
        for count, payment in enumerate(get_payment_list(message.from_user.id))
    ]
    if payments:
        bot_text = '\n'.join(['Твой список платежей:'] + payments)
    else:
        bot_text = 'Твой список платежей пуст'
    await bot.send_message(
        message.chat.id,
        bot_text,
        reply_markup=get_payments_markup()
    )
    await bot.set_state(message.from_user.id, PaymentStates.payment_list, message.chat.id)


@bot.message_handler(state=PaymentStates.payment_list, text_contains=[Button.add_new_payment])
async def pre_payment_add(message):
    bot_text = [
        'Добавьте платёж в следующем формате:',
        'Интернет,Оплата за интернет,650,2020-01-07',
        '',
        'Примеры:',
        'Мобильный интернет,Оплата за мобильный интернет,450.35,2020-01-07',
        'Я.Плюс,Оплата за подписку Яндекс.Плюс,300,2020-01-07',
    ]
    await bot.reply_to(
        message,
        '\n'.join(bot_text),
        reply_markup=get_payments_markup(),
    )
    await bot.set_state(message.from_user.id, PaymentStates.payment_add, message.chat.id)


@bot.message_handler(state=PaymentStates.payment_add)
async def payment_add(message):
    name, description, price, date_payment = message.text.replace(', ', ',').split(',')
    date_payment = datetime.strptime(date_payment, '%Y-%m-%d')
    price = float(price)
    payment = add_payment(message.from_user.id, name, description, price, date_payment)
    logger.debug(f'Add payment {name} for user {payment.user.username}')
    await bot.send_message(
        message.chat.id,
        'Новая оплата добавлена!',
        reply_markup=get_payments_markup()
    )
    await bot.set_state(message.from_user.id, PaymentStates.payment_list, message.chat.id)


@bot.message_handler(state=PaymentStates.payment_list, text_contains=[Button.delete_payment])
async def pre_payment_delete(message):
    await bot.reply_to(
        message,
        'Напиши номер сервиса, который хочешь удалить',
        reply_markup=types.ForceReply(),
    )
    await bot.set_state(message.from_user.id, PaymentStates.payment_delete, message.chat.id)


@bot.message_handler(state=PaymentStates.payment_delete, is_reply=True)
async def payment_delete(message):
    bot_text = list()
    try:
        payment_number = int(message.text)
        delete_result = delete_payment(message.from_user.id, payment_number)
        if delete_result:
            bot_text.append('Удалено выполнено')
        else:
            bot_text.append('Удалено прервано')
    except ValueError:
        bot_text.append('Ошибка! Некорректный номер сервиса')
    except IndexError:
        bot_text.append('Ошибка! Такого номера сервиса нет')

    await bot.send_message(
        message.chat.id,
        '\n'.join(bot_text),
        reply_markup=get_payments_markup(),
    )
    await bot.set_state(message.from_user.id, PaymentStates.payment_list, message.chat.id)