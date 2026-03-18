from __future__ import annotations

import pytest

from backend.src.infrastructure.blog import (
    _build_meta,
    _dump,
    _parse_header,
    _safe_slug,
)


class TestParseHeader:
    def test_standard_post(self) -> None:
        raw = "---\ntitle: Hello\ndate: 2026-01-01\ntags: a, b\n---\nBody here"
        meta, body = _parse_header(raw)
        assert meta == {"title": "Hello", "date": "2026-01-01", "tags": "a, b"}
        assert body == "Body here"

    def test_no_header(self) -> None:
        raw = "Just plain markdown"
        meta, body = _parse_header(raw)
        assert meta == {}
        assert body == "Just plain markdown"

    def test_unclosed_header(self) -> None:
        raw = "---\ntitle: Oops\nno closing"
        meta, body = _parse_header(raw)
        assert meta == {}
        assert body == raw

    def test_empty_body(self) -> None:
        raw = "---\ntitle: Empty\n---\n"
        meta, body = _parse_header(raw)
        assert meta["title"] == "Empty"
        assert body == ""

    def test_colon_in_value(self) -> None:
        raw = "---\ntitle: My Post: The Sequel\ndate: 2026-01-01\n---\nContent"
        meta, body = _parse_header(raw)
        assert meta["title"] == "My Post: The Sequel"

    def test_bom_stripped(self) -> None:
        raw = "\ufeff---\ntitle: BOM\n---\nText"
        meta, body = _parse_header(raw)
        assert meta["title"] == "BOM"
        assert body == "Text"

    def test_empty_value(self) -> None:
        raw = "---\ntitle: \ndate: 2026-01-01\n---\nBody"
        meta, body = _parse_header(raw)
        assert meta["title"] == ""
        assert meta["date"] == "2026-01-01"

    def test_line_without_colon_skipped(self) -> None:
        raw = "---\ntitle: Test\nsome garbage\ndate: 2026-01-01\n---\nBody"
        meta, body = _parse_header(raw)
        assert "title" in meta
        assert "date" in meta
        assert len(meta) == 2

    def test_multiline_body_preserved(self) -> None:
        raw = "---\ntitle: Test\n---\nLine 1\n\nLine 2\n\nLine 3"
        _, body = _parse_header(raw)
        assert "Line 1" in body
        assert "Line 2" in body
        assert "Line 3" in body

    def test_empty_string(self) -> None:
        meta, body = _parse_header("")
        assert meta == {}
        assert body == ""


class TestBuildMeta:
    def test_all_fields(self) -> None:
        raw = {
            "title": "Test",
            "date": "2026-03-01",
            "tags": "python, fastapi, ddd",
            "description": "A description",
            "cover": "https://example.com/img.jpg",
        }
        meta = _build_meta(raw, "fallback-slug")
        assert meta.title == "Test"
        assert meta.date == "2026-03-01"
        assert meta.tags == ["python", "fastapi", "ddd"]
        assert meta.description == "A description"
        assert meta.cover == "https://example.com/img.jpg"

    def test_fallback_title_from_slug(self) -> None:
        meta = _build_meta({}, "my-cool-post")
        assert meta.title == "My Cool Post"

    def test_empty_tags(self) -> None:
        meta = _build_meta({"tags": ""}, "slug")
        assert meta.tags == []

    def test_missing_date_defaults_to_unknown(self) -> None:
        meta = _build_meta({}, "slug")
        assert meta.date == "Unknown"

    def test_single_tag(self) -> None:
        meta = _build_meta({"tags": "python"}, "slug")
        assert meta.tags == ["python"]

    def test_tags_with_extra_spaces(self) -> None:
        meta = _build_meta({"tags": "  python ,  fastapi  , ddd "}, "slug")
        assert meta.tags == ["python", "fastapi", "ddd"]


class TestDump:
    def test_roundtrip(self) -> None:
        original_meta = {"title": "Test", "date": "2026-01-01", "tags": "a, b"}
        original_body = "Hello **world**"
        dumped = _dump(original_meta, original_body)
        parsed_meta, parsed_body = _parse_header(dumped)
        assert parsed_meta == original_meta
        assert parsed_body == original_body

    def test_format(self) -> None:
        result = _dump({"title": "Hi"}, "Body")
        assert result == "---\ntitle: Hi\n---\n\nBody"

    def test_empty_body(self) -> None:
        result = _dump({"title": "Hi"}, "")
        parsed_meta, parsed_body = _parse_header(result)
        assert parsed_meta["title"] == "Hi"

    def test_multiple_fields(self) -> None:
        meta = {"title": "T", "date": "2026-01-01", "tags": "a, b"}
        result = _dump(meta, "text")
        parsed_meta, _ = _parse_header(result)
        assert parsed_meta == meta


class TestSafeSlug:
    @pytest.mark.parametrize(
        "slug",
        [
            "hello-world",
            "my_post",
            "post123",
            "a",
            "ABC",
        ],
    )
    def test_valid_slugs(self, slug: str) -> None:
        assert _safe_slug(slug) == slug

    @pytest.mark.parametrize(
        "slug",
        [
            "",
            "  ",
            "../etc/passwd",
            "hello/world",
            "hello\\world",
            "..",
            "hello\0world",
            "hello world",
            "hello.world",
        ],
    )
    def test_invalid_slugs(self, slug: str) -> None:
        assert _safe_slug(slug) is None

    def test_strips_whitespace(self) -> None:
        assert _safe_slug("  hello  ") == "hello"
