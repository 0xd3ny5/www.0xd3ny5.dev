import uuid

import fastapi
from dependency_injector import wiring
from fastapi import responses

from backend.config import containers
from backend.src.application import dtos, use_cases
from backend.src.domain import uow as uow_
from backend.src.infrastructure import blog
from backend.src.presentation import dependencies

router = fastapi.APIRouter(
    prefix="/admin",
    dependencies=[fastapi.Depends(dependencies.require_admin)],
)


def _reader(request: fastapi.Request) -> blog.BlogReader:
    return request.app.state.blog_reader


@router.get("", response_class=responses.HTMLResponse)
@wiring.inject
async def admin_dashboard(
    request: fastapi.Request,
    uow: uow_.IProjectUnitOfWork = fastapi.Depends(
        wiring.Provide[containers.ApplicationContainer.project_uow]
    ),
) -> fastapi.Response:
    projects = await use_cases.get_all_projects(uow)
    posts = _reader(request).list_posts_meta()
    return request.app.state.templates.TemplateResponse(
        request,
        "admin/dashboard.html",
        {"projects": projects, "posts": posts},
    )


@router.get("/projects/new", response_class=responses.HTMLResponse)
async def admin_new_project(request: fastapi.Request) -> fastapi.Response:
    return request.app.state.templates.TemplateResponse(
        request,
        "admin/work_form.html",
        {"project": None, "is_edit": False},
    )


@router.post("/projects/new")
@wiring.inject
async def admin_create_project(
    request: fastapi.Request,
    title: str = fastapi.Form(...),
    short_description: str = fastapi.Form(...),
    full_description: str = fastapi.Form(""),
    tags: str = fastapi.Form(""),
    github_url: str = fastapi.Form(""),
    live_url: str = fastapi.Form(""),
    cover_image: str = fastapi.Form(""),
    is_featured: bool = fastapi.Form(False),
    is_published: bool = fastapi.Form(False),
    sort_order: int = fastapi.Form(0),
    uow: uow_.IProjectUnitOfWork = fastapi.Depends(
        wiring.Provide[containers.ApplicationContainer.project_uow]
    ),
) -> fastapi.Response:
    data = dtos.ProjectCreateDTO(
        title=title,
        short_description=short_description,
        full_description=full_description,
        tags=[t.strip() for t in tags.split(",") if t.strip()],
        github_url=github_url,
        live_url=live_url,
        cover_image=cover_image,
        is_featured=is_featured,
        is_published=is_published,
        sort_order=sort_order,
    )
    await use_cases.create_project(data, uow)
    return responses.RedirectResponse(url="/admin", status_code=303)


@router.get("/projects/{project_id}/edit", response_class=responses.HTMLResponse)
@wiring.inject
async def admin_edit_project_form(
    request: fastapi.Request,
    project_id: uuid.UUID,
    uow: uow_.IProjectUnitOfWork = fastapi.Depends(
        wiring.Provide[containers.ApplicationContainer.project_uow]
    ),
) -> fastapi.Response:
    project = await use_cases.get_project_by_id(project_id, uow)
    if project is None:
        raise fastapi.HTTPException(status_code=404, detail="Project not found")
    return request.app.state.templates.TemplateResponse(
        request,
        "admin/work_form.html",
        {"project": project, "is_edit": True},
    )


@router.post("/projects/{project_id}/edit")
@wiring.inject
async def admin_update_project(
    project_id: uuid.UUID,
    title: str = fastapi.Form(...),
    short_description: str = fastapi.Form(...),
    full_description: str = fastapi.Form(""),
    tags: str = fastapi.Form(""),
    github_url: str = fastapi.Form(""),
    live_url: str = fastapi.Form(""),
    cover_image: str = fastapi.Form(""),
    is_featured: bool = fastapi.Form(False),
    is_published: bool = fastapi.Form(False),
    sort_order: int = fastapi.Form(0),
    uow: uow_.IProjectUnitOfWork = fastapi.Depends(
        wiring.Provide[containers.ApplicationContainer.project_uow]
    ),
) -> fastapi.Response:
    data = dtos.ProjectUpdateDTO(
        id=project_id,
        title=title,
        short_description=short_description,
        full_description=full_description,
        tags=[t.strip() for t in tags.split(",") if t.strip()],
        github_url=github_url,
        live_url=live_url,
        cover_image=cover_image,
        is_featured=is_featured,
        is_published=is_published,
        sort_order=sort_order,
    )
    await use_cases.update_project(data, uow)
    return responses.RedirectResponse(url="/admin", status_code=303)


@router.post("/projects/{project_id}/delete")
@wiring.inject
async def admin_delete_project(
    project_id: uuid.UUID,
    uow: uow_.IProjectUnitOfWork = fastapi.Depends(
        wiring.Provide[containers.ApplicationContainer.project_uow]
    ),
) -> fastapi.Response:
    await use_cases.delete_project(project_id, uow)
    return responses.RedirectResponse(url="/admin", status_code=303)


@router.post("/projects/{project_id}/toggle-publish")
@wiring.inject
async def admin_toggle_publish(
    project_id: uuid.UUID,
    uow: uow_.IProjectUnitOfWork = fastapi.Depends(
        wiring.Provide[containers.ApplicationContainer.project_uow]
    ),
) -> fastapi.Response:
    project = await use_cases.get_project_by_id(project_id, uow)
    if project is None:
        raise fastapi.HTTPException(status_code=404, detail="Project not found")
    data = dtos.ProjectUpdateDTO(id=project_id, is_published=not project.is_published)
    await use_cases.update_project(data, uow)
    return responses.RedirectResponse(url="/admin", status_code=303)


@router.get("/blog/new", response_class=responses.HTMLResponse)
async def admin_new_post(request: fastapi.Request) -> fastapi.Response:
    return request.app.state.templates.TemplateResponse(
        request,
        "admin/post_form.html",
        {"post": None, "is_edit": False},
    )


@router.post("/blog/new")
async def admin_create_post(
    request: fastapi.Request,
    slug: str = fastapi.Form(...),
    title: str = fastapi.Form(...),
    date: str = fastapi.Form(""),
    tags: str = fastapi.Form(""),
    description: str = fastapi.Form(""),
    cover: str = fastapi.Form(""),
    body: str = fastapi.Form(""),
) -> fastapi.Response:
    safe_slug = "".join(
        c for c in slug.strip().lower().replace(" ", "-") if c.isalnum() or c == "-"
    )
    if not safe_slug:
        raise fastapi.HTTPException(status_code=400, detail="Invalid slug")
    reader = _reader(request)
    if (reader._dir / f"{safe_slug}.md").exists():
        raise fastapi.HTTPException(status_code=400, detail="Post with this slug already exists")
    reader.write_post(safe_slug, title, date, tags, description, cover, body)
    return responses.RedirectResponse(url="/admin", status_code=303)


@router.get("/blog/{slug}/edit", response_class=responses.HTMLResponse)
async def admin_edit_post(request: fastapi.Request, slug: str) -> fastapi.Response:
    post = _reader(request).read_raw(slug)
    if not post:
        raise fastapi.HTTPException(status_code=404, detail="Post not found")
    return request.app.state.templates.TemplateResponse(
        request,
        "admin/post_form.html",
        {"post": post, "is_edit": True},
    )


@router.post("/blog/{slug}/edit")
async def admin_update_post(
    request: fastapi.Request,
    slug: str,
    title: str = fastapi.Form(...),
    date: str = fastapi.Form(""),
    tags: str = fastapi.Form(""),
    description: str = fastapi.Form(""),
    cover: str = fastapi.Form(""),
    body: str = fastapi.Form(""),
) -> fastapi.Response:
    reader = _reader(request)
    if not (reader._dir / f"{slug}.md").exists():
        raise fastapi.HTTPException(status_code=404, detail="Post not found")
    reader.write_post(slug, title, date, tags, description, cover, body)
    return responses.RedirectResponse(url="/admin", status_code=303)


@router.post("/blog/{slug}/delete")
async def admin_delete_post(request: fastapi.Request, slug: str) -> fastapi.Response:
    if not _reader(request).delete_post(slug):
        raise fastapi.HTTPException(status_code=404, detail="Post not found")
    return responses.RedirectResponse(url="/admin", status_code=303)
