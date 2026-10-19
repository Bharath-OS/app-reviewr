#!/usr/bin/env python3
"""Lightweight API + scraper probe (expanded in Milestone 8)."""

from __future__ import annotations

import argparse
import sys

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(description="AppReviewr health probe")
    parser.add_argument(
        "--api",
        default="http://127.0.0.1:8741/api/health",
        help="API health URL",
    )
    args = parser.parse_args()

    try:
        response = httpx.get(args.api, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        print(f"API OK: {data}")
        return 0
    except Exception as exc:  # noqa: BLE001 — CLI surface
        print(f"API FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
