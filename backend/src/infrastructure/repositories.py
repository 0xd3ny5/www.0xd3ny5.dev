from __future__ import annotations

import typing
import uuid

import sqlalchemy as sa
from sqlalchemy.ext import asyncio as sa_async

from backend.src.domain import repositories
from backend.src.infrastructure import mapper, models

if typing.TYPE_CHECKING:
    from backend.src.domain import entities


class PGProjectRepository(repositories.IProjectRepository):
    __slots__: typing.Sequence[str] = ("_mapper", "_session")

    def __init__(self, session: sa_async.AsyncSession) -> None:
        self._session = session
        self._mapper = mapper.ProjectMapper()

    async def get_published(self) -> list[entities.Project]:
        result = await self._session.execute(
            sa.select(models.ProjectModel)
            .where(models.ProjectModel.is_published)
            .order_by(models.ProjectModel.sort_order, models.ProjectModel.created_at.desc())
        )
        return [self._mapper.to_entity(m) for m in result.scalars().all()]

    async def add(self, entity: entities.Project) -> None:
        model = self._mapper.to_model(entity)
        self._session.add(model)

    async def get_by_id(self, id: uuid.UUID) -> entities.Project | None:
        result = await self._session.execute(
            sa.select(models.ProjectModel).where(models.ProjectModel.id == id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._mapper.to_entity(model)

    async def get_all(self) -> list[entities.Project]:
        result = await self._session.execute(
            sa.select(models.ProjectModel).order_by(
                models.ProjectModel.sort_order, models.ProjectModel.created_at.desc()
            )
        )
        return [self._mapper.to_entity(m) for m in result.scalars().all()]

    async def update(self, entity: entities.Project) -> None:
        result = await self._session.execute(
            sa.select(models.ProjectModel).where(models.ProjectModel.id == entity.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return

        for f, v in entity.model_dump(exclude={"id", "created_at"}).items():
            if f == "tags":
                v = ",".join(entity.tags)
            setattr(model, f, v)

        await self._session.flush()

    async def delete(self, id: uuid.UUID) -> None:
        result = await self._session.execute(
            sa.select(models.ProjectModel).where(models.ProjectModel.id == id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
