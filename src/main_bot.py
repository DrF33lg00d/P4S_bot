import asyncio
import time
from datetime import datetime
from collections import defaultdict


from aiogram import executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, IsReplyFilter, Regexp
from utils.settings import logging, bot, dp, PAYMENTS
from src.states import MainStates, NotificationStates, PaymentStates
from src.buttons import get_main_markup, get_payments_markup, get_notifications_markup, Button
from src.username import create_or_update_user, change_username
from src.notifications import get_notification_list, add_notification, delete_notification
from utils.db import User, Payment, Notification, get_payment_list, add_payment, delete_payment


logger = logging.getLogger(__name__)


def run_bot():
    executor.start_polling(dp, skip_updates=True)


@dp.message_handler(commands='start')
async def start(message: types.Message):
    logger.debug(f'User {message.from_user.id} chose /start command')
    create_or_update_user(message.from_user.id, message.from_user.username)
    await message.reply('Hello there!')
    await main_buttons(message)

async def main_buttons(message: types.Message):
    await bot.send_message(
        message.chat.id,
        'Чего изволите?',
        reply_markup=get_main_markup()
    )


@dp.message_handler(Text(contains=[Button.rename]))
async def pre_change_name(message: types.Message):
    logger.debug(f'User wants change username')
    await message.reply(
        'Ну-ка, и как ты хочешь называться теперь?',
        reply_markup=types.ReplyKeyboardRemove()
    )
    await MainStates.change_name.set()


@dp.message_handler(state=MainStates.change_name)
async def change_name(message: types.Message, state: FSMContext):
    logger.debug(f'User change username to {message.text}')
    change_username(message.from_user.id, message.text)
    await bot.send_message(
        message.chat.id,
        f'Отлично, в случае чего буду к тебе так обращаться!'
    )
    await state.finish()
    await main_buttons(message)


@dp.message_handler(Text(contains=[Button.payments]))
@dp.message_handler(Text(contains=[Button.payments]), state=PaymentStates.list)
async def payments_list(message: types.Message):
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
    await PaymentStates.list.set()


@dp.message_handler(Text(contains=[Button.add_new_payment]), state=PaymentStates.list)
async def pre_payment_add(message: types.Message):
    bot_text = [
        'Добавьте платёж в следующем формате:',
        'Интернет,Оплата за интернет,650,2020-01-07',
        '',
        'Примеры:',
        'Мобильный интернет,Оплата за мобильный интернет,450.35,2020-01-07',
        'Я.Плюс,Оплата за подписку Яндекс.Плюс,300,2020-01-07',
    ]
    await message.reply(
        '\n'.join(bot_text),
        reply_markup=get_payments_markup(),
    )
    await PaymentStates.add.set()


@dp.message_handler(state=PaymentStates.add)
async def payment_add(message: types.Message):
    try:
        name, description, price, date_payment = message.text.replace(', ', ',').split(',')
        date_payment = datetime.strptime(date_payment, '%Y-%m-%d')
        price = float(price)
        payment = add_payment(message.from_user.id, name, description, price, date_payment)
        logger.debug(f'Add payment {name} for user {payment.user.username}')
        message = 'Новая оплата добавлена!'
    except Exception as exc:
        logger.error(f'Cannot parse {message.text}')
        message = 'Что-то пошло не так. Попробуйте ещё раз.'
    await bot.send_message(
        message.chat.id,
        message,
        reply_markup=get_payments_markup()
    )
    await PaymentStates.list.set()


@dp.message_handler(Text(contains=[Button.delete_payment]), state=PaymentStates.list)
async def pre_payment_delete(message: types.Message):
    await bot.reply_to(
        message,
        'Напиши номер сервиса, который хочешь удалить',
        reply_markup=types.ForceReply(),
    )
    await PaymentStates.delete.set()


@dp.message_handler(IsReplyFilter(True), state=PaymentStates.delete)
async def payment_delete(message: types.Message):
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

    await message.reply(
        '\n'.join(bot_text),
        reply_markup=get_payments_markup(),
    )
    await PaymentStates.list.set()


@dp.message_handler(Text(contains=[Button.move_back]), state=PaymentStates.list)
async def move_back(message: types.Message, state: FSMContext):
    await state.finish()
    await main_buttons(message)


@dp.message_handler(Text(contains=[Button.move_back]), state=NotificationStates.list)
async def move_back_to_payments(message: types.Message):
    await payments_list(message)


@dp.message_handler(Text(contains=[Button.notifications]), state=PaymentStates.list)
async def pre_notification_list(message: types.Message):
    await message.reply(
        'Напиши номер сервиса, чтобы посмотреть список нотификаций',
        reply_markup=types.ForceReply(),
    )
    await PaymentStates.select.set()

@dp.message_handler(Text(contains=[Button.move_back]), state=NotificationStates.list)
async def move_back_from_notif(message: types.Message):
    if PAYMENTS.get(message.from_user.id):
        PAYMENTS.pop(message.from_user.id)
    await PaymentStates.list.set()
    await payments_list(message)

@dp.message_handler(Text(contains=[Button.add_notification]), state=NotificationStates.list)
async def pre_notification_add(message: types.Message):
    await message.reply(
        'За сколько дней нужно уведомить тебя об оплате?',
        reply_markup=types.ForceReply(),
    )
    await NotificationStates.add.set()


@dp.message_handler(state=NotificationStates.add)
async def notification_add(message: types.Message):
    try:
        payment: Payment = PAYMENTS.get(message.from_user.id)['payment']
        day_before_notification = int(message.text)
        add_notification(payment, day_before_notification)
        bot_message = 'Уведомление добавлено!'
    except (TypeError, IndexError, TypeError):
        bot_message = 'Ошибка добавления уведомления, попробуйте ещё раз'

    PAYMENTS.get(message.from_user.id)['timestamp'] = time.time()
    await bot.send_message(
        message.chat.id,
        bot_message,
        reply_markup=get_notifications_markup(),
    )
    await NotificationStates.list.set()


@dp.message_handler(Text(contains=[Button.delete_notification]),state=NotificationStates.list)
async def pre_notification_delete(message: types.Message):
    await message.reply(
        'Какое уведомление из списка хочешь удалить?',
        reply_markup=types.ForceReply(),
    )
    await NotificationStates.delete.set()


@dp.message_handler(state=NotificationStates.delete)
async def notification_delete(message: types.Message):
    try:
        payment: Payment = PAYMENTS.get(message.from_user.id)['payment']
        notification_number = int(message.text) - 1
        assert delete_notification(payment, notification_number)
    except (TypeError, IndexError, TypeError, AssertionError):
        await bot.send_message(
            message.chat.id,
            'Ошибка удаления уведомления, попробуйте ещё раз',
            reply_markup=get_notifications_markup(),
        )
        await bot.set_state(message.from_user.id, NotificationStates.list, message.chat.id)
        return
    PAYMENTS.get(message.from_user.id)['timestamp'] = time.time()
    await bot.send_message(
            message.chat.id,
            'Уведомление удалено!',
            reply_markup=get_notifications_markup(),
    )
    await NotificationStates.list.set()


@dp.message_handler(state=NotificationStates.list)
@dp.message_handler(Regexp(r'^\d+$'), state=PaymentStates.select)
async def notification_list(message: types.Message):
    bot_text = list()
    notification_list = list()
    error: bool = False
    try:
        payment = get_payment_list(message.from_user.id)[int(message.text)-1]
        notification_list = get_notification_list(payment)
    except ValueError:
        bot_text.append('Ошибка! Некорректный номер сервиса')
        error = True
    except IndexError:
        bot_text.append('Ошибка! Такого номера сервиса нет')
        error = True
    if error:
        await bot.send_message(
            message.chat.id,
            '\n'.join(bot_text),
            reply_markup=get_payments_markup(),
        )
        await PaymentStates.list.set()
    else:
        PAYMENTS[message.from_user.id] = {
            'payment': payment,
            'timestamp': time.time()
        }
        if notification_list:
            bot_text.append('Появление уведомлений к сервису за:')
            bot_text = [f'{index+1}.\t{notif.day_before_payment} день/дней' for index, notif in enumerate(notification_list)]
        else:
            bot_text.append('Уведомления отсутствуют')
        await bot.send_message(
            message.chat.id,
            '\n'.join(bot_text),
            reply_markup=get_notifications_markup(),
        )
        await NotificationStates.list.set()

@dp.message_handler()
async def cannot_parse(message: types.Message, state: FSMContext):
    await bot.send_message(
        message.chat.id,
        'Прости, не понимаю что ты от меня хочешь.\nДавай по новой.',
        reply_markup=get_main_markup()
    )
    await state.finish()
