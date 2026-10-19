"""Tier 1 source unit tests with fixtures / mocks."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
import respx

from app.models import AppRef, Store
from app.sources.apple_tier1 import AppleTier1Source
from app.sources.play_tier1 import PlayTier1Source

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str):
    return json.loads((FIXTURES / name).read_text())


@pytest.mark.asyncio
async def test_play_get_app_info_maps_fields() -> None:
    fixture = _load("play_app_spotify.json")
    source = PlayTier1Source()
    with patch("app.sources.play_tier1.play_app", return_value=fixture):
        info = await source.get_app_info(
            AppRef(
                store=Store.GOOGLE_PLAY,
                app_id="com.spotify.music",
                country="us",
                language="en",
            )
        )
    assert info.name == fixture["title"]
    assert info.developer == fixture["developer"]
    assert info.store == Store.GOOGLE_PLAY


@pytest.mark.asyncio
async def test_play_iter_reviews() -> None:
    batch = _load("play_reviews_spotify.json")
    source = PlayTier1Source()
    with patch(
        "app.sources.play_tier1.play_reviews",
        return_value=(batch, None),
    ):
        reviews = [
            r
            async for r in source.iter_reviews(
                AppRef(store=Store.GOOGLE_PLAY, app_id="com.spotify.music", country="us"),
                max_reviews=3,
                app_name="Spotify",
            )
        ]
    assert len(reviews) == 3
    assert reviews[0].store == Store.GOOGLE_PLAY
    assert reviews[0].review_id
    assert 1 <= reviews[0].rating <= 5


@pytest.mark.asyncio
@respx.mock
async def test_apple_get_app_info() -> None:
    payload = _load("apple_lookup_spotify.json")
    respx.get("https://itunes.apple.com/lookup").mock(
        return_value=httpx.Response(200, json=payload)
    )
    source = AppleTier1Source()
    try:
        info = await source.get_app_info(
            AppRef(store=Store.APP_STORE, app_id="324684580", country="us")
        )
    finally:
        await source.aclose()
    assert info.name.startswith("Spotify")
    assert info.app_id == "324684580"


@pytest.mark.asyncio
@respx.mock
async def test_apple_iter_reviews_from_rss() -> None:
    rss = _load("apple_rss_spotify_page1.json")
    empty = _load("apple_rss_empty.json")

    def _respond(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "/page=1/" in url:
            return httpx.Response(200, json=rss)
        return httpx.Response(200, json=empty)

    respx.get(url__regex=r".*itunes\.apple\.com/.*/rss/customerreviews/.*").mock(
        side_effect=_respond
    )
    source = AppleTier1Source()
    try:
        reviews = [
            r
            async for r in source.iter_reviews(
                AppRef(store=Store.APP_STORE, app_id="324684580", country="us"),
                max_reviews=10,
                app_name="Spotify",
            )
        ]
    finally:
        await source.aclose()
    assert len(reviews) == 2
    assert reviews[0].title == "Love it"
    assert reviews[0].rating == 5
    assert reviews[1].rating == 2


@pytest.mark.asyncio
@respx.mock
async def test_apple_empty_rss_yields_nothing() -> None:
    empty = _load("apple_rss_empty.json")
    respx.get(url__regex=r".*itunes\.apple\.com/.*/rss/customerreviews/.*").mock(
        return_value=httpx.Response(200, json=empty)
    )
    source = AppleTier1Source()
    try:
        reviews = [
            r
            async for r in source.iter_reviews(
                AppRef(store=Store.APP_STORE, app_id="324684580", country="us"),
                max_reviews=50,
            )
        ]
    finally:
        await source.aclose()
    assert reviews == []
