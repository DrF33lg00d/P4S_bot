from contextlib import suppress
from datetime import date
from typing import Optional

from peewee import (
    Model, CharField, AutoField, IntegerField, FloatField, DateField,
    ForeignKeyField, IntegrityError
)
from apscheduler.triggers.cron import CronTrigger

from utils.settings import database
from src.scheduler import scheduler, send_notification


class BaseModel(Model):
    class Meta:
        database = database


class User(BaseModel):
    id = AutoField()
    telegram_id = IntegerField(unique=True)
    username = CharField(default='Default User')

    def get_payment_list(self) -> list[object]:
        payments: Payment = (Payment.select()
                    .join(User)
                    .where(User.telegram_id == self.telegram_id)
                    .order_by(Payment.id)
                    )
        return payments

    def add_payment(self, name: str, description: str, price: float,
                    date) -> object:
        payment: Payment = Payment.create(
            name=name,
            description=description,
            price=price,
            date=date,
            user=self,
        )
        return payment

    def delete_payment(self, payment_number: int) -> bool:
        payment_item = self.get_payment_list()[payment_number-1]
        return bool(payment_item.delete_instance())


class Payment(BaseModel):
    id = AutoField()
    name = CharField(unique=True)
    description = CharField()
    price = FloatField()
    date = DateField(default=date.today())
    user = ForeignKeyField(User, backref='payments', on_delete='cascade')

    def get_notification_list(self) -> list[object]:
        notifications: Notification = (Notification.select()
                    .join(Payment)
                    .where(Payment.id == self.id)
                    .order_by(Notification.id)
                    )
        return notifications

    def add_notification(self, days_before: int) -> Optional[object]:
        if 0 >= days_before or days_before >= 20:
            return None
        notification: Notification = Notification.get_or_create(payment=self, day_before_payment=days_before)[0]
        notification.add_job()
        return notification

    def delete_notification(self, notification_number: int) -> bool:
        try:
            notification = self.get_notification_list()[notification_number]
        except IndexError:
            return False
        notification.delete_notif_job()
        return bool(notification.delete_instance())


class Notification(BaseModel):
    id = AutoField()
    day_before_payment = IntegerField(default=1)
    payment = ForeignKeyField(Payment, backref='notifications', on_delete='cascade')

    def get_job_name(self) -> str:
        return f'u{self.id}p{self.payment.id}n{self.payment.user.id}'

    def delete_notif_job(self):
        with suppress(Exception):
            scheduler.remove_job(self.get_job_name())

    def add_job(self) -> None:
        # TODO: Change schedule trigger after debug
        cron = CronTrigger(
            year='*',
            month='*',
            day='*',
            hour='*',
            minute='*',
            second='0',
        )
        job_id = self.get_job_name()
        message_objects: dict = {
            'telegram_id': self.payment.user.telegram_id,
            'username': self.payment.user.username,
            'payment_name': self.payment.name,
            'payment_price': self.payment.price,
            'notif_days': self.day_before_payment,
        }

        scheduler.add_job(
            send_notification,
            kwargs=message_objects,
            trigger=cron,
            name=job_id,
            id=job_id,
        )


def create_or_update_user(telegram_id: int, username: str):
    user = {
        'telegram_id': telegram_id,
    }
    if username:
        user.update({'username': username})
    with suppress(IntegrityError) as unique_error:
        User.get_or_create(**user)
    del user


database.connect()
database.create_tables([User, Payment, Notification])
