#!/usr/bin/env python3
"""API + Tier 1 scraper health probe."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import httpx


def check_api(url: str) -> dict[str, Any]:
    response = httpx.get(url, timeout=10.0)
    response.raise_for_status()
    return {"ok": True, "body": response.json()}


def check_play() -> dict[str, Any]:
    from google_play_scraper import app as play_app

    info = play_app("com.spotify.music", lang="en", country="us")
    return {
        "ok": bool(info.get("title")),
        "title": info.get("title"),
        "ratings": info.get("ratings"),
    }


def check_apple_lookup() -> dict[str, Any]:
    response = httpx.get(
        "https://itunes.apple.com/lookup",
        params={"id": "324684580", "country": "us"},
        timeout=15.0,
        headers={"User-Agent": "AppReviewr/0.1"},
    )
    response.raise_for_status()
    data = response.json()
    results = data.get("results") or []
    return {
        "ok": bool(results),
        "title": (results[0].get("trackName") if results else None),
    }


def check_apple_rss() -> dict[str, Any]:
    url = (
        "https://itunes.apple.com/us/rss/customerreviews/"
        "page=1/id=324684580/sortBy=mostRecent/json"
    )
    response = httpx.get(
        url, timeout=15.0, headers={"User-Agent": "AppReviewr/0.1"}
    )
    response.raise_for_status()
    entries = (response.json().get("feed") or {}).get("entry") or []
    if isinstance(entries, dict):
        entries = [entries]
    reviews = [e for e in entries if "im:rating" in e]
    return {
        "ok": True,
        "http_status": response.status_code,
        "review_entries": len(reviews),
        "note": (
            "empty RSS feed — Apple Tier 1 reviews may return zero"
            if not reviews
            else "rss ok"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="AppReviewr health probe")
    parser.add_argument(
        "--api",
        default="http://127.0.0.1:8741/api/health",
        help="API health URL",
    )
    parser.add_argument(
        "--scrapers",
        action="store_true",
        help="Also probe Play + Apple Tier 1 endpoints",
    )
    args = parser.parse_args()

    report: dict[str, Any] = {}
    failed = False

    try:
        report["api"] = check_api(args.api)
        print("API OK:", json.dumps(report["api"]["body"]))
    except Exception as exc:  # noqa: BLE001
        report["api"] = {"ok": False, "error": str(exc)}
        print("API FAIL:", exc, file=sys.stderr)
        failed = True

    if args.scrapers:
        for name, fn in [
            ("play", check_play),
            ("apple_lookup", check_apple_lookup),
            ("apple_rss", check_apple_rss),
        ]:
            try:
                report[name] = fn()
                print(f"{name.upper()} OK:", json.dumps(report[name]))
                if name == "apple_rss" and report[name].get("review_entries") == 0:
                    # Not a hard failure — escalate note only
                    print(
                        "NOTE: Apple RSS returned 0 reviews (known Tier 1 limit).",
                        file=sys.stderr,
                    )
            except Exception as exc:  # noqa: BLE001
                report[name] = {"ok": False, "error": str(exc)}
                print(f"{name.upper()} FAIL:", exc, file=sys.stderr)
                failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
