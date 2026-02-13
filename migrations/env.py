import sys
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from alembic import context

# Добавляем путь к папке src, чтобы импорты вида "notifications.*" работали
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Теперь можно импортировать модули проекта как notifications
from notifications.common.config import settings
from notifications.db.models import Base

# Импортируем все модули, где есть модели (каждый импорт регистрирует их в Base.metadata)
# Добавьте другие модули с моделями, если они есть (например, из campaign_scheduler)

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_sync_database_url() -> str:
    db_url = settings.db_dsn
    if db_url.startswith("postgresql+asyncpg://"):
        return db_url.replace("+asyncpg", "+psycopg2")
    return db_url


def run_migrations_offline() -> None:
    url = get_sync_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    sync_database_url = get_sync_database_url()
    connectable = create_engine(sync_database_url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
