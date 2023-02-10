import time
from contextlib import suppress

from pytz import utc
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.triggers.cron import CronTrigger
from utils.settings import dp, logging, get_day_word, PAYMENTS, CACHE_CLEAR_TIMER
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
    job_clear_cache()


async def send_notification(telegram_id: int, payment_price: float,
                            username: str, payment_name: str, notif_days: int):
    days_left: str = f'{notif_days} {get_day_word(notif_days)}'
    message = (
        f'Привет, {username}!',
        f'Оплата по сервису {payment_name} произойдёт через {days_left}.',
        f'Стоимость: {payment_price}',
    )
    try:
        await dp.bot.send_message(
            telegram_id,
            '\n'.join(message),
            reply_markup=get_main_markup()
        )
    except Exception as exc:
        error_message = (
            str(exc),
            f'Cannot send message about notification to user {telegram_id} about {payment_name}'
        )
        logger.debug('\n'.join(error_message))


def job_clear_cache():
    cron = CronTrigger(
        year='*',
        month='*',
        day='*',
        hour='*',
        minute='*/5',
        second='0',
    )
    scheduler.add_job(
        clear_cache,
        trigger=cron,
        name='clear_cache',
        id='clear_cache',
    )


def clear_cache():
    id_list = tuple(PAYMENTS.keys())
    for telegram_id in id_list:
        if time.time() - PAYMENTS[telegram_id]['timestamp'] > CACHE_CLEAR_TIMER:
            PAYMENTS.pop(telegram_id)
    del id_list
