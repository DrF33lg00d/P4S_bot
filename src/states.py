from aiogram.dispatcher.filters.state import State, StatesGroup


class MainStates(StatesGroup):
    main_menu = State()
    change_name = State()
    broadcast = State()


class NotificationStates(StatesGroup):
    list = State()
    add = State()
    delete = State()


class PaymentStates(StatesGroup):
    list = State()
    add = State()
    select = State()
    delete = State()
