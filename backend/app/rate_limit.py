"""Shared SlowAPI limiter instance."""

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings

settings = get_settings()

# Disable in pytest / when APPREVIEW_DISABLE_RATE_LIMIT=1
_enabled = os.getenv("APPREVIEW_DISABLE_RATE_LIMIT", "").lower() not in {
    "1",
    "true",
    "yes",
}

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.rate_limit_per_ip] if _enabled else [],
    enabled=_enabled,
)
