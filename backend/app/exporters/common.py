"""Shared export helpers — filenames, field order, formula injection guard."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from app.models import Review, Store

CSV_HEADERS = [
    "store",
    "app_id",
    "app_name",
    "review_id",
    "author",
    "rating",
    "title",
    "text",
    "date",
    "app_version",
    "thumbs_up",
    "developer_reply",
    "reply_date",
    "country",
    "language",
]

_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def sanitize_cell(value: object | None) -> str:
    """Stringify and neutralize spreadsheet formula injection."""
    if value is None:
        return ""
    text = str(value)
    if text and text[0] in _FORMULA_PREFIXES:
        return "'" + text
    return text


def review_row(review: Review) -> dict[str, str]:
    data = review.model_dump(mode="json")
    return {key: sanitize_cell(data.get(key)) for key in CSV_HEADERS}


def slugify(name: str, fallback: str = "app") -> str:
    slug = _SLUG_RE.sub("-", name.lower()).strip("-")
    return (slug[:48] or fallback)


def export_filename(app_name: str, store: Store, ext: str) -> str:
    date = datetime.now(timezone.utc).strftime("%Y%m%d")
    store_slug = "play" if store == Store.GOOGLE_PLAY else "appstore"
    return f"appreviewr_{slugify(app_name)}_{store_slug}_{date}.{ext}"
