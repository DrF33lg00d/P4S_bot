from telebot.asyncio_handler_backends import State, StatesGroup

from utils.db import User, Payment, Notification
from src.payments import get_payment_list


class NotificationStates(StatesGroup):
    notification_select = State()
    notification_list = State()
    notification_add = State()
    notification_change = State()
    notification_delete = State()


def get_notification_list(user_id: int, payment_number: int) -> list[Notification]:
    payment = get_payment_list(user_id)[payment_number]
    notifications = (Notification.select()
                .join(Payment)
                .where(Payment.id == payment.id)
                .order_by(Notification.id)
                )
    return notifications
