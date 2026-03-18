import uuid

import fastapi
from dependency_injector import wiring
from fastapi import responses

from backend.config import containers
from backend.src.application import use_cases
from backend.src.domain import uow as uow_
from backend.src.presentation import schemas

router = fastapi.APIRouter()


@router.get("/projects/{project_id}", response_class=responses.HTMLResponse)
@wiring.inject
async def project_detail(
    request: fastapi.Request,
    project_id: uuid.UUID,
    uow: uow_.IProjectUnitOfWork = fastapi.Depends(
        wiring.Provide[containers.ApplicationContainer.project_uow]
    ),
) -> fastapi.Response:
    project = await use_cases.get_project_by_id(project_id, uow)
    if project is None:
        raise fastapi.HTTPException(status_code=404, detail="Project not found.")
    return request.app.state.templates.TemplateResponse(
        request,
        "work_detail.html",
        {"project": schemas.to_project_response(project), "active_page": "projects"},
    )


@router.get("/api/projects", response_model=list[schemas.ProjectListItem])
@wiring.inject
async def api_projects(
    uow: uow_.IProjectUnitOfWork = fastapi.Depends(
        wiring.Provide[containers.ApplicationContainer.project_uow]
    ),
) -> list[schemas.ProjectListItem]:
    projects = await use_cases.get_published_projects(uow)
    return [schemas.to_project_list_item(p) for p in projects]
