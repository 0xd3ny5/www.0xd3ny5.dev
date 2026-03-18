import typing
import uuid

import pydantic

from backend.src.infrastructure import timezone

from backend.src.domain import entities


class ProjectResponse(pydantic.BaseModel):
    id: uuid.UUID
    title: str
    short_description: str
    full_description: str
    tags: list[str]
    github_url: str
    live_url: str
    cover_image: str
    is_featured: bool
    is_published: bool
    sort_order: int
    created_at: str


class ProjectListItem(pydantic.BaseModel):
    id: uuid.UUID
    title: str
    short_description: str
    tags: list[str]
    is_featured: bool


def to_project_response(entity: entities.Project) -> ProjectResponse:
    created = ""
    if entity.created_at:
        created = timezone.as_tz(entity.created_at).strftime("%Y-%m-%d")
    return ProjectResponse(
        id=entity.id,
        title=entity.title,
        short_description=entity.short_description,
        full_description=entity.full_description,
        tags=entity.tags,
        github_url=entity.github_url,
        live_url=entity.live_url,
        cover_image=entity.cover_image,
        is_featured=entity.is_featured,
        is_published=entity.is_published,
        sort_order=entity.sort_order,
        created_at=created,
    )


def to_project_list_item(entity: entities.Project) -> ProjectListItem:
    return ProjectListItem(
        id=entity.id,
        title=entity.title,
        short_description=entity.short_description,
        tags=entity.tags,
        is_featured=entity.is_featured,
    )
