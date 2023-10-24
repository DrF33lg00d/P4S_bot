from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData


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

MainMenuCallback = CallbackData('id', 'action')
PaymentView = CallbackData('view', 'id')
PaymentAction = CallbackData('payment', 'action')
NotificationAction = CallbackData('notification', 'action')
NotificationDays = CallbackData('notification', 'day')


def get_main_markup() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    user_rename = InlineKeyboardButton(Button.rename, callback_data=MainMenuCallback.new(action='change_name'))
    payments_list = InlineKeyboardButton(Button.payments, callback_data=MainMenuCallback.new(action='show_payments'))
    markup.add(user_rename, payments_list)
    return markup


def get_admin_markup() -> InlineKeyboardMarkup:
    markup = get_main_markup()
    markup.add(InlineKeyboardButton(Button.broadcast, callback_data=MainMenuCallback.new(action='broadcast')))
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
            callback_data=PaymentView.new(id=i),
        )
        for i in range(len(list_services))
        ]
    markup.add(*buttons)
    add_button = InlineKeyboardButton('Добавить', callback_data=PaymentAction.new(action='add'))
    back_button = InlineKeyboardButton('Вернуться', callback_data=PaymentAction.new(action='back'))
    markup.add(add_button)
    markup.add(back_button)
    return markup

def get_service_markup(has_notifications: bool = True) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(2)
    buttons = [
        InlineKeyboardButton(
            'Добавить уведомление',
            callback_data=NotificationAction.new(action='add'),
        ),
    ]
    if has_notifications:
        buttons.append(
            InlineKeyboardButton(
                'Удалить уведомление',
                callback_data=NotificationAction.new(action='delete'),
            )
        )
    buttons.extend([
        InlineKeyboardButton(
            'Удалить',
            callback_data=PaymentAction.new(action='delete'),
        ),
        InlineKeyboardButton(
            'Вернуться',
            callback_data=PaymentAction.new(action='back'),
        )
    ])
    markup.add(*buttons)
    return markup

def get_notification_days_add(exclude_days: list[int] = list()) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(5)
    buttons = [
        InlineKeyboardButton(
            i,
            callback_data=NotificationDays.new(day=i),
        )
        for i in range(1, 11) if i not in exclude_days
    ]
    markup.add(*buttons)
    return markup


def get_notification_days_delete(days_list: list[int]) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(5)
    buttons = [
        InlineKeyboardButton(
            day,
            callback_data=NotificationDays.new(day=day),
        )
        for day in days_list
    ]
    markup.add(*buttons)
    return markup
