from __future__ import annotations

import uuid

import pytest

from backend.src.application import use_cases
from backend.src.application.dtos import ProjectCreateDTO, ProjectUpdateDTO
from backend.src.domain.entities import Project


@pytest.fixture
def create_dto() -> ProjectCreateDTO:
    return ProjectCreateDTO(
        title="New Project",
        short_description="A new project",
        tags=["python"],
        is_published=True,
    )


class TestCreateProject:
    async def test_creates_and_commits(self, fake_uow, create_dto) -> None:
        result = await use_cases.create_project(create_dto, fake_uow)
        assert result.title == "New Project"
        assert result.tags == ["python"]
        assert fake_uow.committed is True

    async def test_project_stored(self, fake_uow, create_dto) -> None:
        result = await use_cases.create_project(create_dto, fake_uow)
        stored = await fake_uow.projects.get_by_id(result.id)
        assert stored is not None
        assert stored.title == "New Project"


class TestUpdateProject:
    async def test_updates_existing(self, fake_uow, sample_project) -> None:
        await fake_uow.projects.add(sample_project)
        dto = ProjectUpdateDTO(id=sample_project.id, title="Updated")
        result = await use_cases.update_project(dto, fake_uow)
        assert result is not None
        assert result.title == "Updated"
        assert result.is_featured == sample_project.is_featured

    async def test_returns_none_for_missing(self, fake_uow) -> None:
        dto = ProjectUpdateDTO(id=uuid.uuid4(), title="Ghost")
        result = await use_cases.update_project(dto, fake_uow)
        assert result is None

    async def test_partial_update(self, fake_uow, sample_project) -> None:
        await fake_uow.projects.add(sample_project)
        dto = ProjectUpdateDTO(id=sample_project.id, is_published=False)
        result = await use_cases.update_project(dto, fake_uow)
        assert result is not None
        assert result.is_published is False
        assert result.title == sample_project.title


class TestDeleteProject:
    async def test_deletes_existing(self, fake_uow, sample_project) -> None:
        await fake_uow.projects.add(sample_project)
        result = await use_cases.delete_project(sample_project.id, fake_uow)
        assert result is True
        assert await fake_uow.projects.get_by_id(sample_project.id) is None

    async def test_returns_false_for_missing(self, fake_uow) -> None:
        result = await use_cases.delete_project(uuid.uuid4(), fake_uow)
        assert result is False


class TestGetProjects:
    async def test_get_all(self, fake_uow) -> None:
        for i in range(3):
            await fake_uow.projects.add(Project(title=f"P{i}"))
        result = await use_cases.get_all_projects(fake_uow)
        assert len(result) == 3

    async def test_get_published_only(self, fake_uow) -> None:
        await fake_uow.projects.add(Project(title="Published", is_published=True))
        await fake_uow.projects.add(Project(title="Draft", is_published=False))
        result = await use_cases.get_published_projects(fake_uow)
        assert len(result) == 1
        assert result[0].title == "Published"

    async def test_get_by_id(self, fake_uow, sample_project) -> None:
        await fake_uow.projects.add(sample_project)
        result = await use_cases.get_project_by_id(sample_project.id, fake_uow)
        assert result is not None
        assert result.id == sample_project.id

    async def test_get_by_id_missing(self, fake_uow) -> None:
        result = await use_cases.get_project_by_id(uuid.uuid4(), fake_uow)
        assert result is None

    async def test_empty_repo(self, fake_uow) -> None:
        assert await use_cases.get_all_projects(fake_uow) == []
        assert await use_cases.get_published_projects(fake_uow) == []
