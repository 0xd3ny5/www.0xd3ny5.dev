from __future__ import annotations

import typing
import uuid

from backend.src.domain import entities

if typing.TYPE_CHECKING:
    from backend.src.application import dtos
    from backend.src.domain import uow as uow_


async def create_project(
    data: dtos.ProjectCreateDTO,
    uow: uow_.IProjectUnitOfWork,
) -> entities.Project:
    entity = entities.Project(**data.model_dump())
    async with uow:
        await uow.projects.add(entity)
        await uow.commit()
    return entity


async def update_project(
    data: dtos.ProjectUpdateDTO,
    uow: uow_.IProjectUnitOfWork,
) -> entities.Project | None:
    async with uow:
        project = await uow.projects.get_by_id(data.id)
        if project is None:
            return None
        updated = project.model_copy(update=data.model_dump(exclude_unset=True, exclude={"id"}))
        await uow.projects.update(updated)
        await uow.commit()
        return updated


async def delete_project(
    project_id: uuid.UUID,
    uow: uow_.IProjectUnitOfWork,
) -> bool:
    async with uow:
        project = await uow.projects.get_by_id(project_id)
        if project is None:
            return False
        await uow.projects.delete(project_id)
        await uow.commit()
        return True


async def get_all_projects(
    uow: uow_.IProjectUnitOfWork,
) -> list[entities.Project]:
    async with uow:
        return await uow.projects.get_all()


async def get_published_projects(
    uow: uow_.IProjectUnitOfWork,
) -> list[entities.Project]:
    async with uow:
        return await uow.projects.get_published()


async def get_project_by_id(
    project_id: uuid.UUID,
    uow: uow_.IProjectUnitOfWork,
) -> entities.Project | None:
    async with uow:
        return await uow.projects.get_by_id(project_id)
