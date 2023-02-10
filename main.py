from src.main_bot import run_bot
from src.scheduler import start as schedule_start
from utils.db import Notification

def main():
    schedule_start()
    for notitication in Notification.select():
        notitication.add_job()
    run_bot()


if __name__ == '__main__':
    main()
