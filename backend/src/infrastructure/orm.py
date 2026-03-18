from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext import asyncio as sa_async


class Base(orm.DeclarativeBase):
    """Declarative base for all ORM models."""


def create_async_engine(url: str, echo: bool) -> sa_async.AsyncEngine:
    engine_ = sa_async.create_async_engine(
        url,
        echo=echo,
        # Enable connection health checks to avoid using stale DB connections
        pool_pre_ping=True,
        # For small projects (like this portfolio website) we
        # disable SQLAlchemy connection pooling. Using NullPool
        # ensures that each DB operation opens a fresh connection
        # and closes it immediately, which is simpler and more
        # reliable for low-traffic applications.
        poolclass=sa.NullPool,
    )
    return engine_


def create_async_session(
    engine_: sa_async.AsyncEngine,
) -> sa_async.async_sessionmaker[sa_async.AsyncSession]:
    session = sa_async.async_sessionmaker(
        engine_,
        class_=sa_async.AsyncSession,
        expire_on_commit=False,
    )
    return session
