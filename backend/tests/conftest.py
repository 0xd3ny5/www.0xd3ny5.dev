from __future__ import annotations

import typing
import uuid
from pathlib import Path

import pytest
import typing_extensions

from backend.src.domain import entities, repositories
from backend.src.domain import uow as uow_


class FakeProjectRepository(repositories.IProjectRepository):
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, entities.Project] = {}

    async def add(self, entity: entities.Project) -> None:
        self._store[entity.id] = entity

    async def get_by_id(self, id: uuid.UUID) -> entities.Project | None:
        return self._store.get(id)

    async def get_all(self) -> list[entities.Project]:
        return list(self._store.values())

    async def get_published(self) -> list[entities.Project]:
        return [p for p in self._store.values() if p.is_published]

    async def update(self, entity: entities.Project) -> None:
        self._store[entity.id] = entity

    async def delete(self, id: uuid.UUID) -> None:
        self._store.pop(id, None)


class FakeUnitOfWork(uow_.IProjectUnitOfWork):
    def __init__(self) -> None:
        self.projects = FakeProjectRepository()
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self) -> typing_extensions.Self:
        return self

    async def __aexit__(self, *args: typing.Any) -> None:
        pass

    async def _commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True


@pytest.fixture
def fake_uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


@pytest.fixture
def sample_project() -> entities.Project:
    return entities.Project(
        id=uuid.uuid4(),
        title="Test Project",
        short_description="Short desc",
        full_description="Full desc",
        tags=["python", "fastapi"],
        github_url="https://github.com/test/test",
        live_url="https://test.com",
        cover_image="https://test.com/cover.jpg",
        is_featured=True,
        is_published=True,
        sort_order=1,
    )


@pytest.fixture
def tmp_blog_dir(tmp_path: Path) -> Path:
    blog_dir = tmp_path / "blog_posts"
    blog_dir.mkdir()
    return blog_dir
