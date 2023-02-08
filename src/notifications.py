from utils.db import Payment, Notification
from src.scheduler import add_notif_job


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
        add_notif_job(notification[0])
        return notification


def delete_notification(payment: Payment, notification_number: int) -> bool:
    try:
        notification = get_notification_list(payment)[notification_number]
    except IndexError:
        return False
    return bool(notification.delete_instance())
