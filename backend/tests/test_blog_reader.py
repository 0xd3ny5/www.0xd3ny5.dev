from __future__ import annotations

from pathlib import Path

import pytest

from backend.src.infrastructure.blog import BlogReader, _render


@pytest.fixture(autouse=True)
def _clear_render_cache() -> None:
    _render.cache_clear()


def _write_post(blog_dir: Path, slug: str, title: str, body: str, **extra: str) -> Path:
    lines = ["---", f"title: {title}"]
    for k, v in extra.items():
        lines.append(f"{k}: {v}")
    lines.extend(["---", "", body])
    p = blog_dir / f"{slug}.md"
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


class TestGetPost:
    def test_existing_post(self, tmp_blog_dir: Path) -> None:
        _write_post(tmp_blog_dir, "hello", "Hello", "## Hi\n\nWorld")
        reader = BlogReader(tmp_blog_dir)
        post = reader.get_post("hello")
        assert post is not None
        assert post["slug"] == "hello"
        assert post["title"] == "Hello"
        assert "<h2>" in post["html"] or "Hi" in post["html"]

    def test_missing_post(self, tmp_blog_dir: Path) -> None:
        reader = BlogReader(tmp_blog_dir)
        assert reader.get_post("nonexistent") is None

    def test_path_traversal_rejected(self, tmp_blog_dir: Path) -> None:
        reader = BlogReader(tmp_blog_dir)
        assert reader.get_post("../etc/passwd") is None
        assert reader.get_post("..") is None
        assert reader.get_post("hello/world") is None

    def test_post_with_tags(self, tmp_blog_dir: Path) -> None:
        _write_post(tmp_blog_dir, "tagged", "Tagged", "Body", tags="python, fastapi")
        reader = BlogReader(tmp_blog_dir)
        post = reader.get_post("tagged")
        assert post is not None
        assert post["tags"] == ["python", "fastapi"]

    def test_post_with_all_meta(self, tmp_blog_dir: Path) -> None:
        _write_post(
            tmp_blog_dir,
            "full",
            "Full Post",
            "Content",
            date="2026-03-15",
            tags="a, b",
            description="A desc",
            cover="https://img.com/1.jpg",
        )
        reader = BlogReader(tmp_blog_dir)
        post = reader.get_post("full")
        assert post is not None
        assert post["date"] == "2026-03-15"
        assert post["description"] == "A desc"
        assert post["cover"] == "https://img.com/1.jpg"

    def test_markdown_rendered_to_html(self, tmp_blog_dir: Path) -> None:
        _write_post(tmp_blog_dir, "md", "MD", "**bold** and *italic*")
        reader = BlogReader(tmp_blog_dir)
        post = reader.get_post("md")
        assert post is not None
        assert "<strong>bold</strong>" in post["html"]
        assert "<em>italic</em>" in post["html"]

    def test_html_sanitised(self, tmp_blog_dir: Path) -> None:
        _write_post(tmp_blog_dir, "xss", "XSS", '<script>alert("xss")</script>')
        reader = BlogReader(tmp_blog_dir)
        post = reader.get_post("xss")
        assert post is not None
        assert "<script>" not in post["html"]


class TestGetAllPosts:
    def test_empty_dir(self, tmp_blog_dir: Path) -> None:
        reader = BlogReader(tmp_blog_dir)
        assert reader.get_all_posts() == []

    def test_nonexistent_dir(self, tmp_path: Path) -> None:
        reader = BlogReader(tmp_path / "nope")
        assert reader.get_all_posts() == []

    def test_sorted_by_date_desc(self, tmp_blog_dir: Path) -> None:
        _write_post(tmp_blog_dir, "old", "Old", "Old post", date="2025-01-01")
        _write_post(tmp_blog_dir, "new", "New", "New post", date="2026-06-01")
        _write_post(tmp_blog_dir, "mid", "Mid", "Mid post", date="2025-06-01")
        reader = BlogReader(tmp_blog_dir)
        posts = reader.get_all_posts()
        assert len(posts) == 3
        assert posts[0]["slug"] == "new"
        assert posts[1]["slug"] == "mid"
        assert posts[2]["slug"] == "old"

    def test_multiple_posts(self, tmp_blog_dir: Path) -> None:
        for i in range(5):
            _write_post(
                tmp_blog_dir, f"post-{i}", f"Post {i}", f"Body {i}", date=f"2026-0{i + 1}-01"
            )
        reader = BlogReader(tmp_blog_dir)
        assert len(reader.get_all_posts()) == 5


class TestListPostsMeta:
    def test_returns_meta_only(self, tmp_blog_dir: Path) -> None:
        _write_post(tmp_blog_dir, "test", "Test Post", "Long body", date="2026-01-01", tags="a, b")
        reader = BlogReader(tmp_blog_dir)
        meta_list = reader.list_posts_meta()
        assert len(meta_list) == 1
        m = meta_list[0]
        assert m["slug"] == "test"
        assert m["title"] == "Test Post"
        assert m["date"] == "2026-01-01"
        assert m["tags"] == "a, b"
        assert "html" not in m
        assert "body" not in m


class TestWritePost:
    def test_creates_file(self, tmp_blog_dir: Path) -> None:
        reader = BlogReader(tmp_blog_dir)
        reader.write_post("new-post", "New Post", "2026-03-15", "python", "A desc", "", "Body text")
        assert (tmp_blog_dir / "new-post.md").exists()

    def test_written_post_readable(self, tmp_blog_dir: Path) -> None:
        reader = BlogReader(tmp_blog_dir)
        reader.write_post(
            "rw", "Read Write", "2026-01-01", "a, b", "Desc", "https://img.com/1.jpg", "Content"
        )
        post = reader.get_post("rw")
        assert post is not None
        assert post["title"] == "Read Write"
        assert post["date"] == "2026-01-01"
        assert post["tags"] == ["a", "b"]
        assert post["description"] == "Desc"
        assert post["cover"] == "https://img.com/1.jpg"

    def test_creates_directory_if_missing(self, tmp_path: Path) -> None:
        blog_dir = tmp_path / "new" / "blog"
        reader = BlogReader(blog_dir)
        reader.write_post("first", "First", "", "", "", "", "Body")
        assert (blog_dir / "first.md").exists()

    def test_invalid_slug_raises(self, tmp_blog_dir: Path) -> None:
        reader = BlogReader(tmp_blog_dir)
        with pytest.raises(ValueError):
            reader.write_post("../evil", "Evil", "", "", "", "", "Body")

    def test_overwrite_existing(self, tmp_blog_dir: Path) -> None:
        reader = BlogReader(tmp_blog_dir)
        reader.write_post("overwrite", "V1", "2026-01-01", "", "", "", "Version 1")
        reader.write_post("overwrite", "V2", "2026-01-01", "", "", "", "Version 2")
        _render.cache_clear()
        post = reader.get_post("overwrite")
        assert post is not None
        assert post["title"] == "V2"

    def test_empty_optional_fields_omitted(self, tmp_blog_dir: Path) -> None:
        reader = BlogReader(tmp_blog_dir)
        reader.write_post("minimal", "Minimal", "", "", "", "", "Body")
        raw = (tmp_blog_dir / "minimal.md").read_text(encoding="utf-8")
        assert "date:" not in raw
        assert "tags:" not in raw
        assert "description:" not in raw
        assert "cover:" not in raw


class TestDeletePost:
    def test_deletes_existing(self, tmp_blog_dir: Path) -> None:
        _write_post(tmp_blog_dir, "doomed", "Doomed", "Goodbye")
        reader = BlogReader(tmp_blog_dir)
        assert reader.delete_post("doomed") is True
        assert not (tmp_blog_dir / "doomed.md").exists()

    def test_returns_false_for_missing(self, tmp_blog_dir: Path) -> None:
        reader = BlogReader(tmp_blog_dir)
        assert reader.delete_post("nonexistent") is False

    def test_rejects_path_traversal(self, tmp_blog_dir: Path) -> None:
        reader = BlogReader(tmp_blog_dir)
        assert reader.delete_post("../etc/passwd") is False


class TestReadRaw:
    def test_returns_raw_body(self, tmp_blog_dir: Path) -> None:
        _write_post(tmp_blog_dir, "raw-test", "Raw", "## Heading\n\nParagraph", date="2026-03-15")
        reader = BlogReader(tmp_blog_dir)
        raw = reader.read_raw("raw-test")
        assert raw is not None
        assert raw["slug"] == "raw-test"
        assert raw["title"] == "Raw"
        assert raw["date"] == "2026-03-15"
        assert "## Heading" in raw["body"]
        assert "Paragraph" in raw["body"]

    def test_returns_none_for_missing(self, tmp_blog_dir: Path) -> None:
        reader = BlogReader(tmp_blog_dir)
        assert reader.read_raw("nope") is None

    def test_rejects_path_traversal(self, tmp_blog_dir: Path) -> None:
        reader = BlogReader(tmp_blog_dir)
        assert reader.read_raw("../../etc/passwd") is None

    def test_unknown_date_returns_empty(self, tmp_blog_dir: Path) -> None:
        _write_post(tmp_blog_dir, "nodate", "No Date", "Body")
        reader = BlogReader(tmp_blog_dir)
        raw = reader.read_raw("nodate")
        assert raw is not None
        assert raw["date"] == ""
