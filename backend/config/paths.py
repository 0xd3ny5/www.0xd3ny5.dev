from __future__ import annotations

import pathlib

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

TEMPLATES_DIR = PROJECT_ROOT / "backend" / "src" / "presentation" / "templates"
STATIC_DIR = PROJECT_ROOT / "static"
BLOG_DIR = PROJECT_ROOT / "blog_posts"
