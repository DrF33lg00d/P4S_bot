import asyncio
from src.main_bot import run_bot
from src.scheduler import start as schedule_start

def main():
    schedule_start()
    run_bot()


if __name__ == '__main__':
    main()
