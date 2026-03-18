from __future__ import annotations

import logging
import typing
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import markdown
import nh3

logger = logging.getLogger(__name__)

_MD_EXTENSIONS = [
    "fenced_code",
    "codehilite",
    "tables",
    "toc",
    "smarty",
    "attr_list",
    "md_in_html",
]

_ALLOWED_TAGS = {
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "p",
    "a",
    "em",
    "strong",
    "code",
    "pre",
    "ul",
    "ol",
    "li",
    "blockquote",
    "hr",
    "br",
    "img",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "div",
    "span",
    "del",
    "sup",
    "sub",
}
_ALLOWED_ATTRS: dict[str, set[str]] = {
    "a": {"href", "title", "target"},
    "img": {"src", "alt", "title"},
    "code": {"class"},
    "pre": {"class"},
    "div": {"class"},
    "span": {"class"},
    "td": {"align"},
    "th": {"align"},
}

_SEP = "---"


@dataclass(frozen=True, slots=True)
class PostMeta:
    title: str
    date: str
    tags: list[str]
    description: str
    cover: str


def _parse_header(raw: str) -> tuple[dict[str, str], str]:
    """Split raw file content into (meta dict, markdown body).

    Expected file layout:
        ---
        key: value
        key: value
        ---
        markdown body...

    1. Strip optional BOM.
    2. If file doesn't open with '---' - no meta, whole text is the body.
    3. Scan for the closing '---' on its own line.
    4. Parse each line between delimiters as 'key: value'.
       Only the first colon splits key from value (so values may contain colons).
    5. Everything after the closing delimiter is the body.
    """
    text = raw.lstrip("\ufeff")

    if not text.startswith(_SEP):
        return {}, text

    rest = text[len(_SEP) :]
    close = rest.find(f"\n{_SEP}")
    if close == -1:
        return {}, text

    header = rest[:close]
    body = rest[close + 1 + len(_SEP) :].lstrip("\n")

    meta: dict[str, str] = {}
    for line in header.strip().splitlines():
        idx = line.find(":")
        if idx == -1:
            continue
        key = line[:idx].strip()
        val = line[idx + 1 :].strip()
        if key:
            meta[key] = val

    return meta, body


def _build_meta(raw: dict[str, str], fallback_slug: str) -> PostMeta:
    tags_str = raw.get("tags", "")
    return PostMeta(
        title=raw.get("title", fallback_slug.replace("-", " ").title()),
        date=raw.get("date", "Unknown"),
        tags=[t.strip() for t in tags_str.split(",") if t.strip()],
        description=raw.get("description", ""),
        cover=raw.get("cover", ""),
    )


def _dump(meta: dict[str, str], body: str) -> str:
    lines = [_SEP]
    for k, v in meta.items():
        lines.append(f"{k}: {v}")
    lines.append(_SEP)
    lines.append("")
    lines.append(body)
    return "\n".join(lines)


def _safe_slug(slug: str) -> str | None:
    slug = slug.strip()
    if not slug or "/" in slug or "\\" in slug or ".." in slug or "\0" in slug:
        return None
    if not all(c.isalnum() or c in "-_" for c in slug):
        return None
    return slug


@lru_cache(maxsize=64)
def _render(path: str, mtime: float) -> dict[str, typing.Any] | None:
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except Exception:
        logger.warning("Failed to read blog post: %s", path)
        return None

    meta_dict, body = _parse_header(raw)
    slug = Path(path).stem
    meta = _build_meta(meta_dict, slug)

    raw_html = markdown.markdown(body, extensions=_MD_EXTENSIONS)
    safe_html = nh3.clean(raw_html, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRS)

    return {
        "slug": slug,
        "title": meta.title,
        "date": meta.date,
        "tags": meta.tags,
        "description": meta.description,
        "cover": meta.cover,
        "html": safe_html,
    }


class BlogReader:
    __slots__ = ("_dir",)

    def __init__(self, blog_dir: Path) -> None:
        self._dir = blog_dir

    def get_post(self, slug: str) -> dict[str, typing.Any] | None:
        safe = _safe_slug(slug)
        if safe is None:
            return None
        md = self._dir / f"{safe}.md"
        if not md.exists():
            return None
        return _render(str(md), md.stat().st_mtime)

    def get_all_posts(self) -> list[dict[str, typing.Any]]:
        if not self._dir.exists():
            return []
        posts = [self.get_post(md.stem) for md in self._dir.glob("*.md")]
        return sorted(
            [p for p in posts if p],
            key=lambda p: p.get("date", ""),
            reverse=True,
        )

    def list_posts_meta(self) -> list[dict[str, str]]:
        if not self._dir.exists():
            return []
        result = []
        for md in sorted(self._dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                raw = md.read_text(encoding="utf-8")
            except Exception:
                logger.warning("Skipping unreadable post: %s", md.name)
                continue
            meta_dict, _ = _parse_header(raw)
            meta = _build_meta(meta_dict, md.stem)
            result.append(
                {
                    "slug": md.stem,
                    "title": meta.title,
                    "date": meta.date,
                    "tags": ", ".join(meta.tags),
                }
            )
        return result

    def write_post(
        self,
        slug: str,
        title: str,
        date: str,
        tags: str,
        description: str,
        cover: str,
        body: str,
    ) -> None:
        safe = _safe_slug(slug)
        if safe is None:
            raise ValueError(f"Invalid slug: {slug!r}")
        self._dir.mkdir(parents=True, exist_ok=True)

        meta: dict[str, str] = {"title": title}
        if date:
            meta["date"] = date
        if tags:
            meta["tags"] = tags
        if description:
            meta["description"] = description
        if cover:
            meta["cover"] = cover

        (self._dir / f"{safe}.md").write_text(
            _dump(meta, body),
            encoding="utf-8",
        )

    def delete_post(self, slug: str) -> bool:
        safe = _safe_slug(slug)
        if safe is None:
            return False
        md = self._dir / f"{safe}.md"
        if not md.exists():
            return False
        md.unlink()
        return True

    def read_raw(self, slug: str) -> dict[str, str] | None:
        safe = _safe_slug(slug)
        if safe is None:
            return None
        md = self._dir / f"{safe}.md"
        if not md.exists():
            return None
        try:
            raw = md.read_text(encoding="utf-8")
        except Exception:
            return None
        meta_dict, body = _parse_header(raw)
        meta = _build_meta(meta_dict, safe)
        return {
            "slug": safe,
            "title": meta.title,
            "date": meta.date if meta.date != "Unknown" else "",
            "tags": ", ".join(meta.tags),
            "description": meta.description,
            "cover": meta.cover,
            "body": body,
        }
