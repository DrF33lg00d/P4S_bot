from telebot.asyncio_handler_backends import State, StatesGroup


class PaymentStates(StatesGroup):
    payment_list = State()
    payment_add = State()
    payment_change = State()
    payment_delete = State()
