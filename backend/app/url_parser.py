"""Parse Google Play / App Store links and raw IDs into AppRef."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

from app.models import AppRef, Store

PLAY_HOSTS = frozenset({"play.google.com", "www.play.google.com"})
APPLE_HOSTS = frozenset(
    {
        "apps.apple.com",
        "itunes.apple.com",
        "www.apps.apple.com",
        "www.itunes.apple.com",
    }
)
ALLOWED_HOSTS = PLAY_HOSTS | APPLE_HOSTS

# Java-style package name (com.example.app)
PLAY_PACKAGE_RE = re.compile(
    r"^(?P<id>[a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z][a-zA-Z0-9_]*)+)$"
)
# Apple numeric track id
APPLE_ID_RE = re.compile(r"^(?P<id>\d{5,15})$")
APPLE_PATH_ID_RE = re.compile(r"/id(?P<id>\d{5,15})(?:[/?#]|$)")
APPLE_COUNTRY_RE = re.compile(r"^/(?P<cc>[a-z]{2})/", re.IGNORECASE)


class ParseError(ValueError):
    """Raised when input is not a supported store link or ID."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def parse_app_url(value: str) -> AppRef:
    """Detect store + app id from a URL, package name, or Apple numeric ID."""
    raw = (value or "").strip()
    if not raw:
        raise ParseError("empty_input", "Paste a Play Store or App Store link (or app ID).")

    # Bare IDs (no scheme)
    if "://" not in raw and "/" not in raw and "?" not in raw:
        return _parse_bare_id(raw)

    # Allow scheme-less URLs like play.google.com/...
    candidate = raw if "://" in raw else f"https://{raw}"
    parsed = urlparse(candidate)
    host = (parsed.hostname or "").lower()

    if host and host not in ALLOWED_HOSTS:
        raise ParseError(
            "host_not_allowed",
            "Only Google Play and Apple App Store links are supported.",
        )

    if host in PLAY_HOSTS:
        return _parse_play_url(candidate, parsed)
    if host in APPLE_HOSTS:
        return _parse_apple_url(candidate, parsed)

    raise ParseError("unsupported_url", "Could not detect Google Play or App Store from that link.")


def _parse_bare_id(raw: str) -> AppRef:
    m = APPLE_ID_RE.match(raw)
    if m:
        return AppRef(store=Store.APP_STORE, app_id=m.group("id"), raw_url=None)
    m = PLAY_PACKAGE_RE.match(raw)
    if m:
        return AppRef(store=Store.GOOGLE_PLAY, app_id=m.group("id"), raw_url=None)
    raise ParseError(
        "invalid_id",
        "Expected a Play package name (com.example.app) or Apple numeric ID.",
    )


def _parse_play_url(raw: str, parsed) -> AppRef:
    qs = parse_qs(parsed.query)
    app_id = (qs.get("id") or [None])[0]
    if not app_id or not PLAY_PACKAGE_RE.match(app_id):
        raise ParseError(
            "missing_play_id",
            "Google Play link must include ?id=<package.name>.",
        )
    lang = (qs.get("hl") or [None])[0]
    country = (qs.get("gl") or [None])[0]
    if country:
        country = country.lower()
    if lang:
        lang = lang.lower()
    return AppRef(
        store=Store.GOOGLE_PLAY,
        app_id=app_id,
        country=country,
        language=lang,
        raw_url=raw,
    )


def _parse_apple_url(raw: str, parsed) -> AppRef:
    path = parsed.path or ""
    m = APPLE_PATH_ID_RE.search(path)
    if not m:
        # Also allow ?id=
        qs = parse_qs(parsed.query)
        qid = (qs.get("id") or [None])[0]
        if qid and APPLE_ID_RE.match(qid):
            app_id = qid
        else:
            raise ParseError(
                "missing_apple_id",
                "App Store link must include /id<number> (e. above apps.apple.com/.../id123).",
            )
    else:
        app_id = m.group("id")

    country = None
    cm = APPLE_COUNTRY_RE.match(path)
    if cm:
        country = cm.group("cc").lower()

    return AppRef(
        store=Store.APP_STORE,
        app_id=app_id,
        country=country,
        language=None,
        raw_url=raw,
    )
