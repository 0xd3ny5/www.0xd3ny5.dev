
import logging

import fastapi
from fastapi import responses

from backend.src.infrastructure import blog, github

logger = logging.getLogger(__name__)

router = fastapi.APIRouter()


@router.get("/about", response_class=responses.HTMLResponse)
async def about(request: fastapi.Request) -> fastapi.Response:
    return request.app.state.templates.TemplateResponse(
        request,
        "about.html",
        {"active_page": "about"},
    )


@router.get("/api/github-stats", response_class=responses.JSONResponse)
async def github_stats(request: fastapi.Request) -> responses.Response:
    client: github.GitHubClient = request.app.state.github_client
    try:
        stats = await client.get_stats()
        return responses.JSONResponse(
            {
                "repos": stats["public_repos"],
                "stars": stats["total_stars"],
                "commits": stats["commits"],
                "followers": stats["followers"],
            }
        )
    except Exception:
        logger.exception("Failed to fetch GitHub stats")
        return responses.JSONResponse({"error": "unavailable"}, status_code=503)


@router.get("/health", response_class=responses.JSONResponse)
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/robots.txt", response_class=responses.HTMLResponse)
async def robots_txt() -> responses.HTMLResponse:
    return responses.HTMLResponse(
        content="User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n",
        media_type="text/plain",
    )


@router.get("/sitemap.xml", response_class=responses.HTMLResponse)
async def sitemap_xml(request: fastapi.Request) -> responses.HTMLResponse:
    reader: blog.BlogReader = request.app.state.blog_reader
    base = str(request.base_url).rstrip("/")
    urls = [
        f"  <url><loc>{base}/</loc></url>",
        f"  <url><loc>{base}/blog</loc></url>",
        f"  <url><loc>{base}/about</loc></url>",
    ]
    for post in reader.get_all_posts():
        urls.append(f"  <url><loc>{base}/blog/{post['slug']}</loc></url>")
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>"
    )
    return responses.HTMLResponse(content=xml, media_type="application/xml")
