from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup


class Button:
    rename = 'Изменить имя'
    payments = 'Список сервисов'
    broadcast = 'Создать глобальное уведомление'
    notifications = 'Список уведомлений'
    add_new_payment = 'Добавить'
    delete_payment = 'Удалить'
    add_notification = 'Добавить уведомление'
    delete_notification = 'Удалить'
    move_back = 'Вернуться'


def get_main_markup() -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(row_width=2)
    user_rename = KeyboardButton(Button.rename)
    payments_list = KeyboardButton(Button.payments)
    markup.add(user_rename, payments_list)
    return markup


def get_admin_markup() -> ReplyKeyboardMarkup:
    markup = get_main_markup()
    markup.add(KeyboardButton(Button.broadcast))
    return markup


def get_payments_markup() -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(row_width=2)
    buttons = [
        KeyboardButton(Button.payments),
        KeyboardButton(Button.add_new_payment),
        KeyboardButton(Button.delete_payment),
        KeyboardButton(Button.notifications),
        KeyboardButton(Button.move_back),
    ]
    markup.add(*buttons)
    return markup


def get_notifications_markup() -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(row_width=3)
    buttons = [
        KeyboardButton(Button.add_notification),
        KeyboardButton(Button.delete_notification),
        KeyboardButton(Button.move_back),
    ]
    markup.add(*buttons)
    return markup


def get_services_markup(list_services: list) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    buttons = [
        InlineKeyboardButton(
            str(i+1),
            callback_data=i,
        )
        for i in range(len(list_services))
        ]
    markup.add(*buttons)
    add_button = InlineKeyboardButton('Добавить', callback_data='add_service')
    markup.add(add_button)
    return markup

def get_service_markup() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(1)
    buttons = [
        InlineKeyboardButton(
            'Добавить уведомление',
            callback_data='add_notification',
        ),
        InlineKeyboardButton(
            'Удалить',
            callback_data='delete_service',
        ),
        InlineKeyboardButton(
            'Вернуться',
            callback_data='back',
        ),
    ]
    markup.add(*buttons)
    return markup
