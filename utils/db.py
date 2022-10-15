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
    description = CharField()
    price = FloatField()
    payment_date = DateField(default=date.today())
    user = ForeignKeyField(User, backref='payments', on_delete='cascade')


class Notification(BaseModel):
    id = AutoField()
    day_before_payment = IntegerField(default=1)
    payment = ForeignKeyField(Payment, backref='notifications', on_delete='cascade')


database.connect()
database.create_tables([User, Payment, Notification])
