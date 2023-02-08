import asyncio
from src.main_bot import run_bot
from src.scheduler import start as schedule_start

async def main():
    schedule_start()
    await run_bot()


if __name__ == '__main__':
    asyncio.run(main())
