from __future__ import annotations

import base64
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.src.infrastructure.blog import BlogReader, _render


@pytest.fixture(autouse=True)
def _clear_render_cache() -> None:
    _render.cache_clear()


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    blog_dir = tmp_path / "blog_posts"
    blog_dir.mkdir()

    with patch.dict(
        "os.environ",
        {
            "DEBUG": "true",
            "SECRET_KEY": "test-secret-key-for-testing",
            "ADMIN_USERNAME": "testadmin",
            "ADMIN_PASSWORD": "testpass",
            "DATABASE_URL": "sqlite+aiosqlite:///",
        },
    ):
        from backend.config.api_config import get_config

        get_config.cache_clear()

        from backend.src.main import create_app

        app = create_app()
        app.state.blog_reader = BlogReader(blog_dir)

        yield TestClient(app, raise_server_exceptions=False)

        get_config.cache_clear()


@pytest.fixture
def blog_dir(client: TestClient) -> Path:
    return client.app.state.blog_reader._dir


def _auth_header(username: str = "testadmin", password: str = "testpass") -> dict[str, str]:
    creds = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {creds}"}


class TestPublicPages:
    def test_health(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_robots_txt(self, client: TestClient) -> None:
        resp = client.get("/robots.txt")
        assert resp.status_code == 200
        assert "User-agent" in resp.text

    def test_sitemap_xml(self, client: TestClient) -> None:
        resp = client.get("/sitemap.xml")
        assert resp.status_code == 200
        assert "urlset" in resp.text

    def test_about_page(self, client: TestClient) -> None:
        resp = client.get("/about")
        assert resp.status_code == 200

    def test_404_page(self, client: TestClient) -> None:
        resp = client.get("/nonexistent-page")
        assert resp.status_code == 404


class TestBlogPages:
    def test_blog_list_empty(self, client: TestClient) -> None:
        resp = client.get("/blog")
        assert resp.status_code == 200

    def test_blog_post_not_found(self, client: TestClient) -> None:
        resp = client.get("/blog/nonexistent")
        assert resp.status_code == 404

    def test_blog_post_found(self, client: TestClient, blog_dir: Path) -> None:
        (blog_dir / "test-post.md").write_text(
            "---\ntitle: Test\ndate: 2026-01-01\n---\n\nHello world",
            encoding="utf-8",
        )
        resp = client.get("/blog/test-post")
        assert resp.status_code == 200
        assert "Test" in resp.text

    def test_blog_path_traversal(self, client: TestClient) -> None:
        resp = client.get("/blog/../../etc/passwd")
        assert resp.status_code in (404, 422)


class TestAdminAuth:
    def test_admin_requires_auth(self, client: TestClient) -> None:
        resp = client.get("/admin")
        assert resp.status_code == 401

    def test_admin_wrong_password(self, client: TestClient) -> None:
        resp = client.get("/admin", headers=_auth_header("testadmin", "wrong"))
        assert resp.status_code == 401

    def test_admin_wrong_username(self, client: TestClient) -> None:
        resp = client.get("/admin", headers=_auth_header("wrong", "testpass"))
        assert resp.status_code == 401


class TestAdminBlogCRUD:
    def test_create_duplicate_slug_rejected(self, client: TestClient, blog_dir: Path) -> None:
        (blog_dir / "existing.md").write_text("---\ntitle: Existing\n---\nBody", encoding="utf-8")
        resp = client.post(
            "/admin/blog/new",
            headers=_auth_header(),
            data={"slug": "existing", "title": "Duplicate", "body": ""},
            follow_redirects=False,
        )
        assert resp.status_code == 400

    def test_delete_nonexistent_post(self, client: TestClient) -> None:
        resp = client.post(
            "/admin/blog/ghost/delete",
            headers=_auth_header(),
            follow_redirects=False,
        )
        assert resp.status_code == 404

    def test_edit_form_loads(self, client: TestClient, blog_dir: Path) -> None:
        (blog_dir / "form-test.md").write_text(
            "---\ntitle: Form Test\ndate: 2026-01-01\n---\nBody",
            encoding="utf-8",
        )
        resp = client.get("/admin/blog/form-test/edit", headers=_auth_header())
        assert resp.status_code == 200
        assert "Form Test" in resp.text

    def test_new_post_form_loads(self, client: TestClient) -> None:
        resp = client.get("/admin/blog/new", headers=_auth_header())
        assert resp.status_code == 200


class TestSecurityHeaders:
    def test_x_content_type_options(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.headers.get("x-frame-options") == "DENY"

    def test_referrer_policy(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    def test_request_id_present(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.headers.get("x-request-id") is not None

    def test_no_hsts_in_debug(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert "strict-transport-security" not in resp.headers
