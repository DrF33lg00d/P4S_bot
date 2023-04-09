import sys

from src.main_bot import run_bot
from src.scheduler import start as schedule_start
from utils.db import initialize_db

def main():
    schedule_start()
    initialize_db()
    run_bot()


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) == 0:
        main()
    if len(args) == 1 and args[0] == 'migrate':
        from migrations import migration_0001
        migration_0001()
