
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

import sys
from pathlib import Path

# Add project root to python path to allow imports
# We are in app/db/migrations/env.py, so project root is 3 levels up
sys.path.append(str(Path(__file__).resolve().parents[3]))

from app.core.config import settings
from app.db.base import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# set the sqlalchemy.url from our settings
# Ensure we use the sync driver for Alembic if using sync engine_from_config
# OR use async engine. But typically alembic runs fine with sync driver for migrations.
# Let's check settings.SQLALCHEMY_DATABASE_URI. It is async (postgresql+asyncpg).
# We need a sync URL for standard alembic run_migrations_online unless using async engine.
# For simplicity, let's convert the async URL to sync for Alembic, or use async engine correctly.
# The previous valid env.py used async_engine_from_config, which is correct for asyncpg.
# However, the user had connectivity issues.
# Let's stick to async_engine_from_config but make sure it connects correctly.

# To support running alembic from venv against docker localhost:
# The URL in settings comes from env vars.
# .env has POSTGRES_SERVER=localhost, so it should work if port is correct.

config.set_main_option("sqlalchemy.url", str(settings.SQLALCHEMY_DATABASE_URI))

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


import asyncio
from sqlalchemy.ext.asyncio import async_engine_from_config

async def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    cmd_line_url = config.get_main_option("sqlalchemy.url")
    if cmd_line_url:
        configuration["sqlalchemy.url"] = cmd_line_url
    else:
        configuration["sqlalchemy.url"] = str(settings.SQLALCHEMY_DATABASE_URI)
    
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
