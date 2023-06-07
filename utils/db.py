from contextlib import suppress
from datetime import date
from typing import Optional

from peewee import (
    Model, CharField, AutoField, IntegerField, FloatField, DateField,
    BooleanField, ForeignKeyField, IntegrityError,
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
    is_admin = BooleanField(default=False)

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

    def change_username(self, new_username: str) -> None:
        self.username = new_username
        self.save()

    @staticmethod
    def create_or_update(telegram_id: int, username: str) -> None:
        user = {
            'telegram_id': telegram_id,
        }
        if username:
            user.update({'username': username})
        with suppress(IntegrityError) as unique_error:
            User.get_or_create(**user)
        del user


class Payment(BaseModel):
    id = AutoField()
    name = CharField(unique=True)
    description = CharField()
    price = FloatField()
    date = DateField(default=date.today())
    user = ForeignKeyField(User, backref='payments', on_delete='CASCADE')

    def get_notification_list(self) -> list[object]:
        notifications: Notification = (Notification.select()
                    .join(Payment)
                    .where(Payment.id == self.id)
                    .order_by(Notification.id)
                    )
        return notifications

    def delete_instance(self, *args, **kwargs) -> bool:
        for notification in self.notifications:
            notification.delete_notif_job()
        return super().delete_instance(args, kwargs)

    def add_notification(self, days_before: int) -> Optional[object]:
        if 0 >= days_before or days_before >= 20:
            return None
        notification: Notification = Notification.get_or_create(payment=self, day_before_payment=days_before)[0]
        notification.add_job()
        return notification

    def delete_notification(self, notification_day: int) -> bool:
        try:
            notification = [filter(lambda n: n.day_before_payment==notification_day, self.get_notification_list())]
        except IndexError:
            return False
        notification.delete_notif_job()
        return bool(notification.delete_instance())


class Notification(BaseModel):
    id = AutoField()
    day_before_payment = IntegerField(default=1)
    payment = ForeignKeyField(Payment, backref='notifications', on_delete='CASCADE')

    def get_job_name(self) -> str:
        return f'u{self.id}p{self.payment.id}n{self.payment.user.id}'

    def delete_notif_job(self):
        with suppress(Exception):
            scheduler.remove_job(self.get_job_name())

    def add_job(self) -> None:
        day: int = self.payment.date.day - self.day_before_payment
        cron = CronTrigger(
            year='*',
            month='*',
            day=day,
            hour='12',
            minute='0',
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





def initialize_db() -> None:
    database.connect()
    database.create_tables([User, Payment, Notification])
    for notitication in Notification.select():
        notitication.add_job()
