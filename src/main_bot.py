import time
from datetime import datetime
from contextlib import suppress

from aiogram import executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, IsReplyFilter, Regexp, ContentTypeFilter
from aiogram.utils import exceptions
from aiogram.utils.callback_data import CallbackData, CallbackDataFilter

from utils.settings import logging, bot, dp, PAYMENTS, get_day_word
from src.states import MainStates, NotificationStates, PaymentStates
from src.buttons import (
    get_main_markup, get_admin_markup, get_payments_markup,
    get_notifications_markup, Button,
    get_services_markup, get_service_markup, PaymentView, PaymentAction, MainMenuCallback
    )
from utils.db import User, Payment, Notification


logger = logging.getLogger(__name__)


def run_bot():
    executor.start_polling(dp, skip_updates=True)


@dp.message_handler(commands='start')
async def start(message: types.Message):
    User.create_or_update(message.from_user.id, message.from_user.username)
    user: User = User.get(telegram_id=message.from_user.id)
    logger.debug(f'User "{user.id}" choose /start command')
    del user
    await main_buttons(message)


async def main_buttons(message: types.Message):
    user: User = User.get_or_none(telegram_id=message.from_user.id)
    if user and user.is_admin:
        await message.answer(
        'Чего изволите, мой господин?',
        reply_markup=get_admin_markup()
    )
    else:
        await message.answer(
            'Чего изволите?',
            reply_markup=get_main_markup()
        )


@dp.callback_query_handler(MainMenuCallback.filter(action=['broadcast']))
async def pre_broadcast(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.message.edit_text(
        'Напиши, что хочешь сообщить всем пользователям.',
    )
    await state.set_state(MainStates.broadcast)
    user: User = User.get(telegram_id=call.from_user.id)
    logger.debug(f'User-{user.id} wants to broadcast')
    del user


@dp.message_handler(state=MainStates.broadcast)
async def broadcast(message: types.Message, state: FSMContext):
    users: list[User] = User.select()
    for user in users:
        with suppress(exceptions.UserDeactivated):
            await bot.send_message(
                user.telegram_id,
                message.text,
            )
    await state.finish()
    del users
    user: User = User.get(telegram_id=message.from_user.id)
    logger.debug(f'User-{user.id} sends message by broadcast')
    await main_buttons(message)
    del user


@dp.callback_query_handler(MainMenuCallback.filter(action=['change_name']))
async def pre_change_name(call: types.CallbackQuery, state: FSMContext):
    user: User = User.get(telegram_id=call.from_user.id)
    logger.debug(f'User "{user.id}" wants change username')
    await call.message.edit_text(
        'Ну-ка, и как ты хочешь называться теперь?',
    )
    await state.set_state(MainStates.change_name)


@dp.message_handler(state=MainStates.change_name)
async def change_name(message: types.Message, state: FSMContext):
    user: User = User.get(telegram_id=message.from_user.id)
    user.change_username(message.text)
    logger.debug(f'User "{user.id}" change username to "{message.text}"')
    await bot.send_message(
        message.chat.id,
        f'Отлично, буду звать тебя "{user.username}"!'
    )
    await state.finish()
    del user
    await main_buttons(message)


@dp.message_handler(Text(contains=[Button.payments]))
@dp.message_handler(Text(contains=[Button.payments]), state=PaymentStates.list)
@dp.callback_query_handler(PaymentAction.filter())
async def payments_list(message: types.Message, state: FSMContext):
    user: User = User.get(telegram_id=message.chat.id)
    logger.debug(f'User "{user.id}" select payments list')
    payments = [
        f'{count + 1}.\t{payment.description}, {payment.date.day} числа'
        for count, payment in enumerate(user.get_payment_list())
    ]
    if payments:
        bot_text = '\n'.join(['Твой список платежей:'] + payments)
    else:
        bot_text = 'Твой список платежей пуст'
    await message.answer(
        bot_text,
        reply_markup=get_services_markup(payments),
    )
    await state.set_state(PaymentStates.list)
    await state.update_data(user_id=user.id)
    del payments, bot_text


@dp.callback_query_handler(PaymentView.filter(), state=PaymentStates.list)
async def show_payment(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    user: User = User.get(telegram_id=call.message.chat.id)
    payment: Payment = user.get_payment_list()[int(callback_data.get('id'))]
    bot_text = [
        'Информация о сервисе:',
        payment.name,
        f'Цена: {payment.price}',
        f'{payment.date.day} числа'
        ]
    await call.message.edit_text(
        '\n'.join(bot_text),
        reply_markup=get_service_markup()
    )
    await state.set_state(PaymentStates.select)
    del payment, bot_text

# @dp.callback_query_handler(state=PaymentStates.select)
# @dp.callback_query_handler(Text('add_notification'), state=PaymentStates.select)



# @dp.callback_query_handler(state=PaymentStates.select)
# @dp.callback_query_handler(Text('delete_service'), state=PaymentStates.select)
# async def delete_payment(call: types.CallbackQuery):
#     await payments_list(call.message)


@dp.callback_query_handler(PaymentAction.filter(action=['back']), state=PaymentStates.select)
async def back_to_list_payments(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(PaymentStates.list)
    await payments_list(call.message, state)




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

        user: User = User.get(telegram_id=message.from_user.id)
        payment: Payment = user.add_payment(name, description, price, date_payment)
        logger.debug(f'Add payment "{name}" for user {user.id}')
        bot_message = f'Новый сервис "{payment.name}" добавлена!'
    except (ValueError, TypeError) as exc:
        logger.error(f'Cannot parse "{message.text}"')
        bot_message = 'Что-то пошло не так. Попробуйте ещё раз.'
    await bot.send_message(
        message.chat.id,
        bot_message,
        reply_markup=get_payments_markup()
    )
    await PaymentStates.list.set()


@dp.message_handler(Text(contains=[Button.delete_payment]), state=PaymentStates.list)
async def pre_payment_delete(message: types.Message):
    await message.reply(
        'Напиши номер сервиса, который хочешь удалить',
        reply_markup=types.ForceReply(),
    )
    await PaymentStates.delete.set()


@dp.message_handler(IsReplyFilter(True), state=PaymentStates.delete)
async def payment_delete(message: types.Message):
    bot_text = list()
    try:
        user: User = User.get(telegram_id=message.from_user.id)
        payment: Payment = user.get_payment_list()[int(message.text)-1]
        delete_result = bool(payment.delete_instance(True))
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
        payment.add_notification(day_before_notification)
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
        assert payment.delete_notification(notification_number)
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
    user: User = User.get(telegram_id=message.from_user.id)
    try:
        payment: Payment = user.get_payment_list()[int(message.text)-1]
        notification_list: list[Notification] = payment.get_notification_list()
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
            bot_text.append(f'Уведомления по сервису "{payment.name}" придут за:')
            bot_text.extend([
                f'{index+1}.\t{notif.day_before_payment} {get_day_word(notif.day_before_payment)}'
                for index, notif in enumerate(notification_list)
            ])
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
