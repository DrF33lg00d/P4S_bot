import peewee
from playhouse.migrate import migrate

from utils.settings import migrator
from utils.db import User


def migration_0001() -> None:
    is_admin_field = peewee.BooleanField(default=False)
    migrate(
        migrator.add_column(User._meta.table_name, 'is_admin', is_admin_field),
    )
