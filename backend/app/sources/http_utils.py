"""Shared HTTP helpers for Tier 1 sources."""

from __future__ import annotations

import asyncio
import random
from collections.abc import Mapping
from typing import Any

import httpx

from app.config import get_settings

USER_AGENTS = (
    "AppReviewr/0.1 (+https://github.com/Bharath-OS/app-reviewr)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
)


def pick_user_agent() -> str:
    return random.choice(USER_AGENTS)


async def request_json(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
) -> tuple[int, Any]:
    """GET/POST JSON with retries, UA rotation, and timeouts from settings."""
    settings = get_settings()
    last_exc: Exception | None = None
    for attempt in range(settings.http_max_retries):
        merged = {"User-Agent": pick_user_agent(), "Accept": "application/json"}
        if headers:
            merged.update(headers)
        try:
            response = await client.request(
                method,
                url,
                params=params,
                headers=merged,
                timeout=settings.http_timeout_seconds,
            )
            if response.status_code in {429, 503, 502}:
                await asyncio.sleep(0.5 * (2**attempt) + random.random() * 0.2)
                continue
            response.raise_for_status()
            return response.status_code, response.json()
        except (httpx.HTTPError, ValueError) as exc:
            last_exc = exc
            await asyncio.sleep(0.4 * (2**attempt))
    assert last_exc is not None
    raise last_exc
