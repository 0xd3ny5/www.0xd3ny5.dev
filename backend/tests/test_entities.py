from __future__ import annotations

import uuid

from backend.src.application.dtos import ProjectCreateDTO, ProjectUpdateDTO
from backend.src.domain.entities import Project
from backend.src.infrastructure.mapper import ProjectMapper
from backend.src.infrastructure.models import ProjectModel


class TestProject:
    def test_default_values(self) -> None:
        p = Project()
        assert p.title == ""
        assert p.is_published is False
        assert p.is_featured is False
        assert p.tags == []
        assert p.sort_order == 0
        assert isinstance(p.id, uuid.UUID)

    def test_from_kwargs(self) -> None:
        p = Project(title="Test", tags=["a", "b"], is_published=True)
        assert p.title == "Test"
        assert p.tags == ["a", "b"]
        assert p.is_published is True

    def test_model_copy_partial_update(self) -> None:
        p = Project(title="Original", is_published=False, sort_order=5)
        updated = p.model_copy(update={"title": "Updated", "is_published": True})
        assert updated.title == "Updated"
        assert updated.is_published is True
        assert updated.sort_order == 5
        assert updated.id == p.id


class TestProjectMapper:
    def test_to_entity(self) -> None:
        model = ProjectModel(
            id=uuid.uuid4(),
            title="Test",
            short_description="Short",
            full_description="Full",
            tags="python,fastapi",
            github_url="https://github.com",
            live_url="https://live.com",
            cover_image="img.jpg",
            is_featured=True,
            is_published=True,
            sort_order=1,
        )
        mapper = ProjectMapper()
        entity = mapper.to_entity(model)
        assert entity.title == "Test"
        assert entity.tags == ["python", "fastapi"]
        assert entity.is_featured is True

    def test_to_model(self) -> None:
        entity = Project(
            title="Test",
            tags=["python", "fastapi"],
            is_published=True,
        )
        mapper = ProjectMapper()
        model = mapper.to_model(entity)
        assert model.title == "Test"
        assert model.tags == "python,fastapi"
        assert model.is_published is True

    def test_roundtrip(self) -> None:
        original = Project(
            title="Roundtrip",
            short_description="Short",
            full_description="Full",
            tags=["a", "b", "c"],
            github_url="https://github.com",
            live_url="https://live.com",
            cover_image="img.jpg",
            is_featured=True,
            is_published=False,
            sort_order=3,
        )
        mapper = ProjectMapper()
        model = mapper.to_model(original)
        restored = mapper.to_entity(model)
        assert restored.title == original.title
        assert restored.tags == original.tags
        assert restored.is_featured == original.is_featured
        assert restored.id == original.id

    def test_empty_tags(self) -> None:
        model = ProjectModel(
            id=uuid.uuid4(),
            title="No Tags",
            short_description="",
            full_description="",
            tags="",
            github_url="",
            live_url="",
            cover_image="",
            is_featured=False,
            is_published=False,
            sort_order=0,
        )
        mapper = ProjectMapper()
        entity = mapper.to_entity(model)
        assert entity.tags == []


class TestDTOs:
    def test_create_dto_defaults(self) -> None:
        dto = ProjectCreateDTO(title="Test")
        assert dto.title == "Test"
        assert dto.short_description == ""
        assert dto.tags == []
        assert dto.is_published is False

    def test_update_dto_partial(self) -> None:
        pid = uuid.uuid4()
        dto = ProjectUpdateDTO(id=pid, title="New Title")
        dumped = dto.model_dump(exclude_unset=True)
        assert "title" in dumped
        assert "short_description" not in dumped
        assert "is_published" not in dumped
