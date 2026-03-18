from __future__ import annotations

import abc
import typing
import uuid

if typing.TYPE_CHECKING:
    from backend.src.domain import entities


class IProjectRepository(abc.ABC):
    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    async def get_published(self) -> list[entities.Project]: ...

    @abc.abstractmethod
    async def add(self, entity: entities.Project) -> None: ...

    @abc.abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> entities.Project | None: ...

    @abc.abstractmethod
    async def get_all(self) -> list[entities.Project]: ...

    @abc.abstractmethod
    async def update(self, entity: entities.Project) -> None: ...

    @abc.abstractmethod
    async def delete(self, id: uuid.UUID) -> None: ...
