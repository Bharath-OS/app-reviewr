"""Google Play Tier 1 source via google-play-scraper."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

from google_play_scraper import Sort
from google_play_scraper import app as play_app
from google_play_scraper import reviews as play_reviews
from google_play_scraper.exceptions import NotFoundError

from app.config import get_settings
from app.models import AppInfo, AppRef, Review, Store
from app.sources.base import ReviewSource
from app.sources.errors import AppNotFoundError, SourceUnavailable

_SORT_MAP = {
    "newest": Sort.NEWEST,
    "most_relevant": Sort.MOST_RELEVANT,
    "rating": Sort.RATING,
}


def _to_iso(value: Any) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    # google-play-scraper often returns naive datetime already handled above;
    # string fallback:
    text = str(value).strip()
    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except ValueError:
        return text


class PlayTier1Source(ReviewSource):
    store = Store.GOOGLE_PLAY

    async def get_app_info(self, app_ref: AppRef) -> AppInfo:
        lang = app_ref.language or "en"
        country = (app_ref.country or "us").lower()
        try:
            data = await asyncio.to_thread(
                play_app, app_ref.app_id, lang=lang, country=country
            )
        except NotFoundError as exc:
            raise AppNotFoundError(
                f"Google Play app '{app_ref.app_id}' was not found."
            ) from exc
        except Exception as exc:  # noqa: BLE001
            raise SourceUnavailable(f"Google Play lookup failed: {exc}") from exc

        return AppInfo(
            store=Store.GOOGLE_PLAY,
            app_id=data.get("appId") or app_ref.app_id,
            name=data.get("title") or app_ref.app_id,
            developer=data.get("developer"),
            icon_url=data.get("icon"),
            rating=data.get("score"),
            rating_count=data.get("ratings"),
            url=data.get("url"),
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
        lang = app_ref.language or "en"
        country = (app_ref.country or "us").lower()
        play_sort = _SORT_MAP.get(sort, Sort.NEWEST)
        filter_score = kwargs.get("filter_score")

        app_name = kwargs.get("app_name") or app_ref.app_id
        continuation = None
        yielded = 0
        page_size = min(200, limit)

        while yielded < limit:
            count = min(page_size, limit - yielded)
            try:
                batch, continuation = await asyncio.to_thread(
                    play_reviews,
                    app_ref.app_id,
                    lang=lang,
                    country=country,
                    sort=play_sort,
                    count=count,
                    filter_score_with=filter_score,
                    continuation_token=continuation,
                )
            except NotFoundError as exc:
                raise AppNotFoundError(
                    f"Google Play app '{app_ref.app_id}' was not found."
                ) from exc
            except Exception as exc:  # noqa: BLE001
                raise SourceUnavailable(f"Google Play reviews failed: {exc}") from exc

            if not batch:
                break

            for item in batch:
                yield self._map_review(item, app_ref, app_name=app_name, country=country, language=lang)
                yielded += 1
                if yielded >= limit:
                    break

            if continuation is None:
                break
            await asyncio.sleep(0.15)

    def _map_review(
        self,
        item: dict[str, Any],
        app_ref: AppRef,
        *,
        app_name: str,
        country: str,
        language: str,
    ) -> Review:
        return Review(
            store=Store.GOOGLE_PLAY,
            app_id=app_ref.app_id,
            app_name=app_name,
            review_id=str(item.get("reviewId") or ""),
            author=str(item.get("userName") or "Anonymous"),
            rating=int(item.get("score") or 1),
            title=None,
            text=str(item.get("content") or ""),
            date=_to_iso(item.get("at")),
            app_version=item.get("appVersion") or item.get("reviewCreatedVersion"),
            thumbs_up=item.get("thumbsUpCount"),
            developer_reply=item.get("replyContent"),
            reply_date=_to_iso(item.get("repliedAt")) if item.get("repliedAt") else None,
            country=country.upper(),
            language=language,
        )
