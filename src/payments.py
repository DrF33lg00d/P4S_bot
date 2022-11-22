from telebot.asyncio_handler_backends import State, StatesGroup

from utils.db import User, Payment


class PaymentStates(StatesGroup):
    payment_list = State()
    payment_add = State()
    payment_change = State()
    payment_delete = State()


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
