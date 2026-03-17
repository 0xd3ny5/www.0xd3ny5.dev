"""Alembic async migration environment."""

from __future__ import annotations

from logging.config import fileConfig

from sqlalchemy import pool, engine_from_config

from alembic import context

from backend.config import api_config
from backend.src.infrastructure import orm

# import all models so Base.metadata is populated
from backend.src.infrastructure.models import ProjectModel # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = api_config.get_config()
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = orm.Base.metadata


def run_migrations_offline():
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=settings.database_url,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()