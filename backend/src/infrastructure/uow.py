from __future__ import annotations

import typing

import typing_extensions
from sqlalchemy.ext import asyncio as sa_async

from backend.src.domain import uow
from backend.src.infrastructure import repositories as repository_impl

if typing.TYPE_CHECKING:
    from backend.src.domain import repositories


class PGProjectUnitOfWork(uow.IProjectUnitOfWork):
    projects: repositories.IProjectRepository
    __slots__: typing.Sequence[str] = ("_session_factory",)

    def __init__(
        self,
        session_factory: typing.Callable[..., sa_async.AsyncSession],
    ) -> None:
        self._session_factory = session_factory

    async def __aenter__(self) -> typing_extensions.Self:
        self.session = self._session_factory()
        self.projects = repository_impl.PGProjectRepository(self.session)
        return await super().__aenter__()

    async def __aexit__(self, *args: typing.Any) -> None:
        await super().__aexit__(*args)
        await self.session.close()

    async def _commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
