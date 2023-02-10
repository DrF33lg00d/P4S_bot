from datetime import date

from peewee import (
    Model, CharField, AutoField, IntegerField, FloatField, DateField, ForeignKeyField
)

from utils.settings import database


class BaseModel(Model):
    class Meta:
        database = database


class User(BaseModel):
    id = AutoField()
    telegram_id = IntegerField(unique=True)
    username = CharField(default='Default User')


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


def get_payment_list(user_id: int) -> list[Payment]:
    payments = (Payment.select()
                .join(User)
                .where(User.telegram_id == user_id)
                .order_by(Payment.id)
                )
    return payments

def add_payment(
        user_id: int,
        name: str,
        description: str,
        price: float,
        date
) -> Payment:
    user = User.get(telegram_id=user_id)
    payment = Payment.create(
        name=name,
        description=description,
        price=price,
        date=date,
        user_id=user,
    )
    return payment


def delete_payment(user_id: int, payment_number: int) -> bool:
    user = User.get(telegram_id=user_id)
    payment_item = get_payment_list(user.telegram_id)[payment_number-1]
    return bool(payment_item.delete_instance())


database.connect()
database.create_tables([User, Payment, Notification])
