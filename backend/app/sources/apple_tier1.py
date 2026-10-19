"""Apple App Store Tier 1 — iTunes lookup + customerreviews RSS JSON.

Honesty note: the public RSS feed historically capped ~500 reviews/country
(10 pages × ~50). As of 2026-10 probing, many regions return an empty feed
(HTTP 200, zero entries). Callers must surface returned counts honestly.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

import httpx
from langdetect import DetectorFactory, LangDetectException, detect

from app.config import get_settings
from app.models import AppInfo, AppRef, Review, Store
from app.sources.base import ReviewSource
from app.sources.errors import AppNotFoundError, SourceUnavailable
from app.sources.http_utils import request_json

DetectorFactory.seed = 0

LOOKUP_URL = "https://itunes.apple.com/lookup"
RSS_URL = (
    "https://itunes.apple.com/{country}/rss/customerreviews/"
    "page={page}/id={app_id}/sortBy={sort}/json"
)
# Apple RSS historically supports pages 1–10 (~50 reviews each).
MAX_RSS_PAGES = 10
_SORT_MAP = {
    "newest": "mostRecent",
    "most_relevant": "mostHelpful",
    "rating": "mostRecent",
}


def _label(node: Any, default: str | None = None) -> str | None:
    if node is None:
        return default
    if isinstance(node, dict):
        if "label" in node:
            return str(node["label"])
        return default
    return str(node)


def _to_iso(value: str | None) -> str:
    if not value:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except ValueError:
        return value


def _detect_language(text: str) -> str | None:
    sample = (text or "").strip()
    if len(sample) < 20:
        return None
    try:
        return detect(sample)
    except LangDetectException:
        return None


class AppleTier1Source(ReviewSource):
    store = Store.APP_STORE

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client
        self._owns_client = client is None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient()
        return self._client

    async def aclose(self) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    async def get_app_info(self, app_ref: AppRef) -> AppInfo:
        country = (app_ref.country or "us").lower()
        client = await self._get_client()
        try:
            _, payload = await request_json(
                client,
                "GET",
                LOOKUP_URL,
                params={"id": app_ref.app_id, "country": country},
            )
        except Exception as exc:  # noqa: BLE001
            raise SourceUnavailable(f"Apple lookup failed: {exc}") from exc

        results = payload.get("results") or []
        if not results:
            raise AppNotFoundError(f"App Store app '{app_ref.app_id}' was not found.")

        item = results[0]
        artwork = (
            item.get("artworkUrl512")
            or item.get("artworkUrl100")
            or item.get("artworkUrl60")
        )
        return AppInfo(
            store=Store.APP_STORE,
            app_id=str(item.get("trackId") or app_ref.app_id),
            name=item.get("trackName") or app_ref.app_id,
            developer=item.get("artistName"),
            icon_url=artwork,
            rating=item.get("averageUserRating"),
            rating_count=item.get("userRatingCount"),
            url=item.get("trackViewUrl"),
        )

    async def iter_reviews(
        self,
        app_ref: AppRef,
        *,
        sort: str = "newest",
        max_reviews: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[Review]:
        settings = get_settings()
        limit = max_reviews or settings.max_reviews_per_job
        limit = min(limit, settings.max_reviews_per_job)
        country = (app_ref.country or "us").lower()
        rss_sort = _SORT_MAP.get(sort, "mostRecent")
        app_name = kwargs.get("app_name") or app_ref.app_id
        client = await self._get_client()

        yielded = 0
        for page in range(1, MAX_RSS_PAGES + 1):
            if yielded >= limit:
                break
            url = RSS_URL.format(
                country=country, page=page, app_id=app_ref.app_id, sort=rss_sort
            )
            try:
                _, payload = await request_json(client, "GET", url)
            except Exception as exc:  # noqa: BLE001
                raise SourceUnavailable(f"Apple RSS failed on page {page}: {exc}") from exc

            entries = (payload.get("feed") or {}).get("entry") or []
            if isinstance(entries, dict):
                entries = [entries]
            review_entries = [e for e in entries if self._is_review_entry(e)]
            if not review_entries:
                break

            for entry in review_entries:
                yield self._map_review(
                    entry,
                    app_ref,
                    app_name=app_name,
                    country=country,
                )
                yielded += 1
                if yielded >= limit:
                    break
            await asyncio.sleep(0.1)

    def _is_review_entry(self, entry: dict[str, Any]) -> bool:
        # First feed entry is often app metadata without im:rating.
        return "im:rating" in entry or (
            "content" in entry and "author" in entry and "im:name" not in entry
        )

    def _map_review(
        self,
        entry: dict[str, Any],
        app_ref: AppRef,
        *,
        app_name: str,
        country: str,
    ) -> Review:
        rating_raw = _label(entry.get("im:rating"), "1") or "1"
        try:
            rating = max(1, min(5, int(float(rating_raw))))
        except ValueError:
            rating = 1
        text = _label(entry.get("content"), "") or ""
        author = _label((entry.get("author") or {}).get("name"), "Anonymous") or "Anonymous"
        review_id = _label(entry.get("id"), "") or ""
        # Sometimes id is nested attributes
        if not review_id and isinstance(entry.get("id"), dict):
            review_id = str((entry["id"].get("attributes") or {}).get("im:id") or "")
        title = _label(entry.get("title"))
        version = _label(entry.get("im:version"))
        updated = _label(entry.get("updated"))

        return Review(
            store=Store.APP_STORE,
            app_id=app_ref.app_id,
            app_name=app_name,
            review_id=review_id or f"apple-{hash((author, text, updated)) & 0xFFFFFFFF:x}",
            author=author,
            rating=rating,
            title=title,
            text=text,
            date=_to_iso(updated),
            app_version=version,
            thumbs_up=None,
            developer_reply=None,
            reply_date=None,
            country=country.upper(),
            language=_detect_language(text),
        )
