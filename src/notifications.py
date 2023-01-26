from telebot.asyncio_handler_backends import State, StatesGroup

from utils.db import Payment, Notification


class NotificationStates(StatesGroup):
    select = State()
    list = State()
    add = State()
    delete = State()


def get_notification_list(payment: Payment) -> list[Notification]:
    notifications = (Notification.select()
                .join(Payment)
                .where(Payment.id == payment.id)
                .order_by(Notification.id)
                )
    return notifications


def add_notification(payment: Payment, days_before: int) -> Notification| None:
    if 0 < days_before < 20:
        notification = Notification.get_or_create(payment=payment, day_before_payment=days_before)
        return notification


def delete_notification(payment: Payment, notification_number: int) -> bool:
    try:
        notification = get_notification_list(payment)[notification_number]
    except IndexError:
        return False
    return bool(notification.delete_instance())
