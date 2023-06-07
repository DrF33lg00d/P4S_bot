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
    get_services_markup, get_service_markup, get_notification_days_add,
    PaymentView, PaymentAction, MainMenuCallback, NotificationAction, NotificationDays
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
    await main_menu(user, message)
    del user


async def main_menu(user: User, message: types.Message):
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
    await main_menu(user, message)
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
    await main_menu(user, message)
    del user


@dp.callback_query_handler(MainMenuCallback.filter(action=['show_payments']))
@dp.callback_query_handler(PaymentAction.filter(action=['back']))
async def payments_list(call: types.CallbackQuery, state: FSMContext):
    user: User = User.get(telegram_id=call.from_user.id)
    logger.debug(f'User "{user.username}" select payments list')
    payments = [
        f'{count + 1}.\t{payment.description}, {payment.date.day} числа'
        for count, payment in enumerate(user.get_payment_list())
    ]
    if payments:
        bot_text = '\n'.join(['Твой список платежей:'] + payments)
    else:
        bot_text = 'Твой список платежей пуст'
    await call.message.edit_text(
        bot_text,
        reply_markup=get_services_markup(payments),
    )
    await state.set_state(PaymentStates.list)
    del payments, bot_text, user


@dp.callback_query_handler(PaymentView.filter(), state=PaymentStates.list)
async def select_payment(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    payment_ordered_number = int(callback_data.get('id'))
    user: User = User.get(telegram_id=call.from_user.id)
    payment: Payment = user.get_payment_list()[payment_ordered_number]
    await call.message.edit_text(
        get_payment_message(payment),
        reply_markup=get_service_markup()
    )
    await state.set_state(PaymentStates.select)
    await state.update_data(payment_ordered_number=payment_ordered_number)
    del payment

def get_payment_message(payment: Payment):
    bot_text = [
        'Информация о сервисе:',
        payment.name,
        f'Цена: {payment.price}',
        f'{payment.date.day} числа'
        ]
    return '\n'.join(bot_text)


@dp.callback_query_handler(MainMenuCallback.filter(action=['back']), state=PaymentStates.list)
async def back_to_main_menu(call: types.CallbackQuery, state: FSMContext):
    user: User = User.get(telegram_id=call.from_user.id)
    await state.finish()
    await call.message.delete()
    await main_menu(user, call.message)


@dp.callback_query_handler(PaymentAction.filter(action=['add']), state=PaymentStates.list)
async def pre_payment_add(call: types.CallbackQuery, state: FSMContext):
    bot_text = [
        'Добавьте платёж в следующем формате:',
        'Название,Описание,Цена,год-месяц-день',
        '',
        'Примеры:',
        'Мобильный интернет,Оплата за мобильный интернет,450.35,2020-01-07',
        'Я.Плюс,Оплата за подписку Яндекс.Плюс,300,2020-01-07',
    ]
    await call.message.edit_text(
        '\n'.join(bot_text),
    )
    await state.set_state(PaymentStates.add)


@dp.message_handler(state=PaymentStates.add)
async def payment_add(message: types.Message, state: FSMContext):
    user: User = User.get(telegram_id=message.from_user.id)
    try:
        name, description, price, date_payment = message.text.replace(', ', ',').split(',')
        date_payment = datetime.strptime(date_payment, '%Y-%m-%d')
        price = float(price)
        payment: Payment = user.add_payment(name, description, price, date_payment)
        logger.debug(f'Add payment "{name}" for user {user.id}')

        bot_message = f'Новый сервис "{payment.name}" добавлен!'
        await message.answer(
            f'{bot_message}\n{get_payment_message(payment)}',
            reply_markup=get_service_markup(),
        )
        await state.set_state(PaymentStates.select)
        del name, description, price, date_payment, user, payment
    except (ValueError, TypeError) as exc:
        logger.error(f'Cannot parse "{message.text}"')
        bot_message = 'Что-то пошло не так. Попробуйте ещё раз.'
        await message.answer(
            bot_message,
        )
        await state.finish()
        await main_menu(user, message)
    del bot_message


@dp.callback_query_handler(PaymentAction.filter(action=['delete']), state=PaymentStates.select)
async def delete_payment(call: types.CallbackQuery, state: FSMContext):
    bot_text = list()
    user_data = await state.get_data()
    payment_ordered_number = user_data['payment_ordered_number']
    try:
        user: User = User.get(telegram_id=call.from_user.id)
        payment: Payment = user.get_payment_list()[payment_ordered_number]
        delete_result = bool(payment.delete_instance(True))
        if delete_result:
            bot_text.append('Удалено выполнено')
        else:
            bot_text.append('Удалено прервано')
    except ValueError:
        bot_text.append('Ошибка! Некорректный номер сервиса')
    except IndexError:
        bot_text.append('Ошибка! Такого номера сервиса нет')
    await call.answer('\n'.join(bot_text))

    await state.set_state(PaymentStates.list)
    await state.reset_data()
    await payments_list(call, state)
    del bot_text, user_data, payment_ordered_number
    del user, payment, delete_result


@dp.callback_query_handler(PaymentAction.filter(action=['back']), state=PaymentStates.select)
async def back_to_payment_list(call: types.CallbackQuery, state: FSMContext):
    await payments_list(call, state)



@dp.callback_query_handler(NotificationAction.filter(action=['add']), state=PaymentStates.select)
async def pre_notification_add(сall: types.CallbackQuery, state: FSMContext):
    await сall.message.edit_text(
        'За сколько дней нужно уведомить тебя об оплате?',
        reply_markup=get_notification_days_add(),
    )
    await state.set_state(NotificationStates.add)


@dp.callback_query_handler(NotificationDays.filter(), state=NotificationStates.add)
async def notification_add(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.message.edit_text('Добавление...')
    user_data = await state.get_data()
    payment_ordered_number = user_data.get('payment_ordered_number')
    user: User = User.get(telegram_id=call.from_user.id)
    payment: Payment = user.get_payment_list()[payment_ordered_number]
    day_before_notification = int(callback_data.get('id'))
    try:
        payment.add_notification(day_before_notification)
        bot_message = 'Уведомление добавлено!'
    except (TypeError, IndexError, TypeError):
        bot_message = 'Ошибка добавления уведомления, попробуйте ещё раз'
    await call.message.edit_text(
        f'{bot_message}\n{get_payment_message(payment)}',
        reply_markup=get_service_markup()
    )
    await state.set_state(PaymentStates.select)
    del payment


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
