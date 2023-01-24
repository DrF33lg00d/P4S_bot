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
