"""Alembic environment configuration for LIFE OS."""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Make sure the `backend` package is on the path when running alembic from
# the backend/ directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Import Base and all models so Alembic can see the full schema.
from backend.database.connection import Base  # noqa: E402
import backend.models  # noqa: E402, F401 — registers all models on Base.metadata

config = context.config

# Override sqlalchemy.url from DATABASE_URL env var (never hardcode credentials)
database_url = os.environ.get("DATABASE_URL", "sqlite:///./lifeos_dev.db")
config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

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


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
