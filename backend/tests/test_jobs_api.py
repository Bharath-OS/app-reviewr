"""Job API integration tests with mocked sources."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.models import AppInfo, Review, Store


def _sample_reviews(n: int = 5) -> list[Review]:
    return [
        Review(
            store=Store.GOOGLE_PLAY,
            app_id="com.spotify.music",
            app_name="Spotify",
            review_id=f"r{i}",
            author=f"User{i}",
            rating=(i % 5) + 1,
            title=None,
            text=f"Review text {i} music",
            date="2024-06-01T12:00:00Z",
            app_version="1.0",
            thumbs_up=0,
            developer_reply="Thanks" if i % 2 == 0 else None,
            reply_date="2024-06-02T12:00:00Z" if i % 2 == 0 else None,
            country="US",
            language="en",
        )
        for i in range(n)
    ]


async def _async_iter(items):
    for item in items:
        yield item
        await asyncio.sleep(0)


def test_create_job_and_complete(client: TestClient) -> None:
    info = AppInfo(
        store=Store.GOOGLE_PLAY,
        app_id="com.spotify.music",
        name="Spotify",
        developer="Spotify AB",
        icon_url="https://example.com/i.png",
        rating=4.5,
        rating_count=100,
        url="https://play.google.com/store/apps/details?id=com.spotify.music",
    )
    reviews = _sample_reviews(8)

    source = MagicMock()
    source.get_app_info = AsyncMock(return_value=info)
    source.iter_reviews = MagicMock(return_value=_async_iter(reviews))
    source.aclose = AsyncMock()

    with patch("app.jobs.get_source", return_value=source):
        created = client.post(
            "/api/jobs",
            json={
                "url": "https://play.google.com/store/apps/details?id=com.spotify.music",
                "filters": {
                    "countries": ["us"],
                    "max_reviews": 5,
                    "keyword": "music",
                },
            },
        )
        assert created.status_code == 200, created.text
        job_id = created.json()["id"]

        # Poll until terminal
        final = None
        for _ in range(50):
            resp = client.get(f"/api/jobs/{job_id}")
            assert resp.status_code == 200
            final = resp.json()
            if final["status"] in {"completed", "failed", "cancelled"}:
                break
            # Give background task time
            import time

            time.sleep(0.05)

    assert final is not None
    assert final["status"] == "completed"
    assert final["review_count"] <= 5
    assert final["app_info"]["name"] == "Spotify"

    page = client.get(f"/api/jobs/{job_id}/reviews")
    assert page.status_code == 200
    body = page.json()
    assert body["total"] == final["review_count"]
    assert len(body["reviews"]) == body["total"]


def test_create_job_invalid_url(client: TestClient) -> None:
    resp = client.post("/api/jobs", json={"url": "https://evil.example/x"})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "host_not_allowed"


def test_rating_filter_uses_separate_cache_and_scrape(client: TestClient) -> None:
    """Mixed cache must not satisfy a later 1★-only request."""
    info = AppInfo(
        store=Store.GOOGLE_PLAY,
        app_id="com.spotify.music",
        name="Spotify",
        developer="Spotify AB",
        icon_url=None,
        rating=4.5,
        rating_count=10,
        url=None,
    )
    mixed = _sample_reviews(10)  # ratings cycle 1..5
    one_star = [
        Review(
            store=Store.GOOGLE_PLAY,
            app_id="com.spotify.music",
            app_name="Spotify",
            review_id=f"one{i}",
            author=f"One{i}",
            rating=1,
            title=None,
            text=f"One star {i}",
            date="2024-06-01T12:00:00Z",
            country="US",
            language="en",
        )
        for i in range(6)
    ]
    calls: list[int | None] = []

    async def tracking_iter(*_a, **kwargs):
        score = kwargs.get("filter_score")
        calls.append(score)
        items = one_star if score == 1 else mixed
        async for item in _async_iter(items):
            yield item

    source = MagicMock()
    source.get_app_info = AsyncMock(return_value=info)
    source.iter_reviews = MagicMock(side_effect=lambda *a, **k: tracking_iter(*a, **k))
    source.aclose = AsyncMock()

    with patch("app.jobs.get_source", return_value=source):
        # 1) Unfiltered mixed fetch → caches under ratings=all
        first = client.post(
            "/api/jobs",
            json={
                "url": "com.spotify.music",
                "filters": {"countries": ["us"], "max_reviews": 10, "sort": "newest"},
            },
        )
        assert first.status_code == 200
        job1 = first.json()["id"]
        for _ in range(40):
            st = client.get(f"/api/jobs/{job1}").json()
            if st["status"] == "completed":
                break
            import time

            time.sleep(0.05)
        assert calls == [None]

        # 2) 1★ only → must scrape with filter_score=1 (not thin the mixed cache)
        second = client.post(
            "/api/jobs",
            json={
                "url": "com.spotify.music",
                "filters": {
                    "countries": ["us"],
                    "max_reviews": 5,
                    "sort": "newest",
                    "ratings": [1],
                },
            },
        )
        assert second.status_code == 200
        job2 = second.json()["id"]
        for _ in range(40):
            st = client.get(f"/api/jobs/{job2}").json()
            if st["status"] in {"completed", "failed"}:
                break
            import time

            time.sleep(0.05)
        assert st["status"] == "completed"
        assert calls == [None, 1]
        assert st["served_from_cache"] is False
        assert st["review_count"] == 5
        assert all(r["rating"] == 1 for r in client.get(f"/api/jobs/{job2}/reviews").json()["reviews"])

        # 3) Same 1★ filters again → cache hit, no third scrape
        third = client.post(
            "/api/jobs",
            json={
                "url": "com.spotify.music",
                "filters": {
                    "countries": ["us"],
                    "max_reviews": 5,
                    "sort": "newest",
                    "ratings": [1],
                },
            },
        )
        job3 = third.json()["id"]
        for _ in range(40):
            st = client.get(f"/api/jobs/{job3}").json()
            if st["status"] in {"completed", "failed"}:
                break
            import time

            time.sleep(0.05)
        assert st["status"] == "completed"
        assert st["served_from_cache"] is True
        assert calls == [None, 1]


def test_second_fetch_uses_cache(client: TestClient) -> None:
    info = AppInfo(
        store=Store.GOOGLE_PLAY,
        app_id="com.spotify.music",
        name="Spotify",
        developer="Spotify AB",
        icon_url=None,
        rating=4.5,
        rating_count=10,
        url=None,
    )
    reviews = _sample_reviews(4)
    calls = {"n": 0}

    async def tracking_iter(*_a, **_k):
        calls["n"] += 1
        async for item in _async_iter(reviews):
            yield item

    source = MagicMock()
    source.get_app_info = AsyncMock(return_value=info)
    source.iter_reviews = MagicMock(side_effect=lambda *a, **k: tracking_iter())
    source.aclose = AsyncMock()

    body = {
        "url": "com.spotify.music",
        "filters": {"countries": ["us"], "max_reviews": 4, "sort": "newest"},
    }

    with patch("app.jobs.get_source", return_value=source):
        first = client.post("/api/jobs", json=body)
        assert first.status_code == 200
        job1 = first.json()["id"]
        for _ in range(40):
            st = client.get(f"/api/jobs/{job1}").json()
            if st["status"] == "completed":
                break
            import time

            time.sleep(0.05)
        assert calls["n"] == 1

        second = client.post("/api/jobs", json=body)
        assert second.status_code == 200
        job2 = second.json()["id"]
        for _ in range(40):
            st = client.get(f"/api/jobs/{job2}").json()
            if st["status"] in {"completed", "failed"}:
                break
            import time

            time.sleep(0.05)
        assert st["status"] == "completed"
        assert st["served_from_cache"] is True
        assert calls["n"] == 1  # scraper not called again
        assert any(n["code"] == "served_from_cache" for n in st["notes"])


def test_job_not_found(client: TestClient) -> None:
    assert client.get("/api/jobs/does-not-exist").status_code == 404


def test_cancel_job(client: TestClient) -> None:
    info = AppInfo(
        store=Store.GOOGLE_PLAY,
        app_id="com.spotify.music",
        name="Spotify",
        developer="Spotify AB",
        icon_url=None,
        rating=4.0,
        rating_count=1,
        url=None,
    )

    async def slow_iter(*_a, **_k):
        for i in range(100):
            yield Review(
                store=Store.GOOGLE_PLAY,
                app_id="com.spotify.music",
                app_name="Spotify",
                review_id=f"s{i}",
                author="U",
                rating=5,
                title=None,
                text="slow",
                date="2024-01-01T00:00:00Z",
                app_version=None,
                thumbs_up=None,
                developer_reply=None,
                reply_date=None,
                country="US",
                language="en",
            )
            await asyncio.sleep(0.05)

    source = MagicMock()
    source.get_app_info = AsyncMock(return_value=info)
    source.iter_reviews = MagicMock(side_effect=lambda *a, **k: slow_iter())
    source.aclose = AsyncMock()

    with patch("app.jobs.get_source", return_value=source):
        created = client.post(
            "/api/jobs",
            json={
                "url": "com.spotify.music",
                "filters": {"countries": ["us"], "max_reviews": 50},
            },
        )
        job_id = created.json()["id"]
        cancelled = client.post(f"/api/jobs/{job_id}/cancel")
        assert cancelled.status_code == 200
        assert cancelled.json()["status"] == "cancelled"


def test_cache_roundtrip(tmp_path) -> None:
    from app.cache import ReviewCache, ratings_cache_key

    assert ratings_cache_key(None) == "all"
    assert ratings_cache_key([3, 1, 1]) == "1+3"
    from app.models import SortOption

    cache = ReviewCache(db_path=tmp_path / "c.db")
    reviews = _sample_reviews(2)
    cache.set(
        Store.GOOGLE_PLAY,
        "com.spotify.music",
        "us",
        "en",
        SortOption.NEWEST,
        reviews,
        ratings_key="all",
    )
    got = cache.get(
        Store.GOOGLE_PLAY,
        "com.spotify.music",
        "us",
        "en",
        SortOption.NEWEST,
        ratings_key="all",
    )
    assert got is not None
    assert len(got) == 2
    assert got[0].review_id == "r0"
    # Different star bucket must not see the mixed payload.
    assert (
        cache.get(
            Store.GOOGLE_PLAY,
            "com.spotify.music",
            "us",
            "en",
            SortOption.NEWEST,
            ratings_key="1",
        )
        is None
    )
