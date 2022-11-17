from telebot.asyncio_handler_backends import State, StatesGroup

from utils.db import User, Payment


class PaymentStates(StatesGroup):
    payment_list = State()
    payment_add = State()
    payment_change = State()
    payment_delete = State()


def get_payment_list(telegram_id: int) -> list[Payment]:
    payments = (Payment.select()
                .join(User)
                .where(User.telegram_id == telegram_id)
                .order_by(Payment.id.desc())
                )
    return payments
