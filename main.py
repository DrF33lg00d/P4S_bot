from src.main_bot import run_bot
from src.scheduler import start as schedule_start
from utils.db import initialize_db

def main():
    schedule_start()
    initialize_db()
    run_bot()


if __name__ == '__main__':
    main()
