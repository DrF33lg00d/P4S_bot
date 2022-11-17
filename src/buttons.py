from telebot.types import ReplyKeyboardMarkup, KeyboardButton


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
    move_back = 'Вернуться'


def get_main_markup() -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(row_width=2)
    user_rename = KeyboardButton(Button.rename)
    payments_list = KeyboardButton(Button.payments)
    markup.add(user_rename, payments_list)
    return markup


def get_payments_markup() -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(row_width=5)
    buttons = [
        KeyboardButton(Button.add_new_payment),
        KeyboardButton(Button.change_payment),
        KeyboardButton(Button.delete_payment),
        KeyboardButton(Button.notifications),
        KeyboardButton(Button.move_back),
    ]
    markup.add(*buttons)
    return markup