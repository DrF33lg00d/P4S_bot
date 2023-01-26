from telebot.types import ReplyKeyboardMarkup, KeyboardButton


class Button:
    rename = 'Изменить имя'
    payments = 'Список сервисов'
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
