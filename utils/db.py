from contextlib import suppress
from datetime import date

from peewee import (
    Model, CharField, AutoField, IntegerField, FloatField, DateField,
    ForeignKeyField, IntegrityError
)

from utils.settings import database


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


class Notification(BaseModel):
    id = AutoField()
    day_before_payment = IntegerField(default=1)
    payment = ForeignKeyField(Payment, backref='notifications', on_delete='cascade')


def create_or_update_user(telegram_id: int, username: str):
    user = {
        'telegram_id': telegram_id,
    }
    if username:
        user.update({'username': username})
    with suppress(IntegrityError) as unique_error:
        User.get_or_create(**user)
    del user


def change_username(telegram_id: int, new_username: str):
    user = User.get_or_create(telegram_id=telegram_id)[0]
    user.username = new_username
    user.save()
    del user



database.connect()
database.create_tables([User, Payment, Notification])
