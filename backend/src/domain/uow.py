import abc
import typing

import typing_extensions

from backend.src.domain import repositories


class IProjectUnitOfWork(abc.ABC):
    projects: repositories.IProjectRepository

    async def __aenter__(self) -> typing_extensions.Self:
        return self

    async def __aexit__(self, *args: typing.Any) -> None:
        await self.rollback()

    async def commit(self) -> None:
        await self._commit()

    @abc.abstractmethod
    async def rollback(self) -> None: ...

    @abc.abstractmethod
    async def _commit(self) -> None: ...
