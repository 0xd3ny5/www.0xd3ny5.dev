
import fastapi
from dependency_injector import wiring
from fastapi import responses

from backend.config import containers
from backend.src.application import use_cases
from backend.src.domain import uow as uow_
from backend.src.infrastructure import timezone

router = fastapi.APIRouter()


@router.get("/", response_class=responses.HTMLResponse)
@wiring.inject
async def home(
    request: fastapi.Request,
    uow: uow_.IProjectUnitOfWork = fastapi.Depends(
        wiring.Provide[containers.ApplicationContainer.project_uow]
    ),
) -> fastapi.Response:
    published_projects = await use_cases.get_published_projects(uow)
    return request.app.state.templates.TemplateResponse(
        request,
        "index.html",
        {
            "projects": published_projects,
            "active_page": "projects",
            "now": timezone.now(),
        },
    )
