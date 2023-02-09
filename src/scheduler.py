from contextlib import suppress

import asyncio
from pytz import utc
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot, Dispatcher
from utils.db import Notification, Payment, User
from utils.settings import MainStates, dp, logging, get_day_word
from src.buttons import get_main_markup


logger = logging.getLogger(__name__)

jobstores = {
    'default': MemoryJobStore()
}
executors = {
    'default': ThreadPoolExecutor(20),
    'processpool': ProcessPoolExecutor(5)
}
job_defaults = {
    'coalesce': False,
    'max_instances': 3
}

scheduler = AsyncIOScheduler(
    jobstores=jobstores,
    # executors=executors,
    # job_defaults=job_defaults,
    timezone=utc
)


def start():
    scheduler.start()


async def send_notification(notification: Notification):
    user: User = notification.payment.user
    days_left: str = f'{notification.day_before_payment} {get_day_word(notification.day_before_payment)}'
    message = (
        f'Привет, {user.username}!',
        f'Оплата по сервису {notification.payment.name} произойдёт через {days_left}.',
        f'Стоимость: {notification.payment.price}',
    )
    try:
        await dp.bot.send_message(
            user.telegram_id,
            '\n'.join(message),
            reply_markup=get_main_markup()
        )
    except Exception as exc:
        error_message = (
            str(exc),
            f'Cannot send message about notification, job_name: {get_job_name(notification)}'
        )
        logger.debug('\n'.join(error_message))


def get_job_name(notif: Notification) -> str:
    return f'u{notif.id}p{notif.payment.id}n{notif.payment.user.id}'

def add_notif_job(notif: Notification):
    # TODO: Change schedule trigger after debug
    cron = CronTrigger(
        year='*',
        month='*',
        day='*',
        hour='*',
        minute='*',
        second='0',
    )
    job_id = get_job_name(notif)
    scheduler.add_job(
        send_notification,
        kwargs={'notification': notif},
        trigger=cron,
        name=job_id,
        id=job_id,
    )

def delete_notif_job(notif: Notification):
    job_id = get_job_name(notif)
    with suppress(Exception):
        scheduler.remove_job(job_id)
