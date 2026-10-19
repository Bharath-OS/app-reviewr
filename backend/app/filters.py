"""Client-side / post-fetch review filters."""

from __future__ import annotations

from datetime import datetime, timezone

from app.models import JobFilters, Review


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        # Allow YYYY-MM-DD
        try:
            dt = datetime.fromisoformat(text + "T00:00:00+00:00")
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def review_matches(review: Review, filters: JobFilters) -> bool:
    if filters.ratings and review.rating not in filters.ratings:
        return False

    if filters.languages:
        lang = (review.language or "").lower()
        if not lang or lang not in {l.lower() for l in filters.languages}:
            return False

    if filters.keyword:
        needle = filters.keyword.lower()
        hay = f"{review.title or ''} {review.text}".lower()
        if needle not in hay:
            return False

    if filters.has_developer_reply is True and not review.developer_reply:
        return False
    if filters.has_developer_reply is False and review.developer_reply:
        return False

    review_dt = _parse_date(review.date)
    date_from = _parse_date(filters.date_from)
    date_to = _parse_date(filters.date_to)
    if date_from and review_dt and review_dt < date_from:
        return False
    if date_to and review_dt and review_dt > date_to:
        return False

    return True


def apply_filters(reviews: list[Review], filters: JobFilters) -> list[Review]:
    return [r for r in reviews if review_matches(r, filters)]


def dedupe_key(review: Review) -> tuple[str, str, str, str]:
    return (review.store.value, review.app_id, review.review_id, review.country.upper())


def dedupe_reviews(reviews: list[Review]) -> list[Review]:
    seen: set[tuple[str, str, str, str]] = set()
    out: list[Review] = []
    for review in reviews:
        key = dedupe_key(review)
        if key in seen:
            continue
        seen.add(key)
        out.append(review)
    return out
