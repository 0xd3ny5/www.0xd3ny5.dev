import fastapi
from fastapi import responses

from backend.src.infrastructure import blog

router = fastapi.APIRouter()


@router.get("/blog", response_class=responses.HTMLResponse)
async def blog_list(request: fastapi.Request) -> fastapi.Response:
    reader: blog.BlogReader = request.app.state.blog_reader
    posts = reader.get_all_posts()
    return request.app.state.templates.TemplateResponse(
        request,
        "blog.html",
        {"posts": posts, "active_page": "blog"},
    )


@router.get("/blog/{slug}", response_class=responses.HTMLResponse)
async def blog_post(request: fastapi.Request, slug: str) -> fastapi.Response:
    reader: blog.BlogReader = request.app.state.blog_reader
    post = reader.get_post(slug)
    if not post:
        raise fastapi.HTTPException(status_code=404, detail="Post not found")
    return request.app.state.templates.TemplateResponse(
        request,
        "post.html",
        {"post": post, "active_page": "blog"},
    )
