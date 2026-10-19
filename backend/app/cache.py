"""SQLite-backed review cache keyed by (store, app_id, country, lang, sort, ratings)."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock

from app.config import get_settings
from app.models import Review, SortOption, Store


def ratings_cache_key(ratings: list[int] | None) -> str:
    """Stable cache segment for star filters.

    - No rating filter → ``all`` (mixed scrape)
    - Specific stars → e.g. ``1`` or ``2+3`` (sorted, deduped)
    """
    if not ratings:
        return "all"
    return "+".join(str(r) for r in sorted({int(r) for r in ratings}))


class ReviewCache:
    def __init__(self, db_path: str | Path | None = None) -> None:
        settings = get_settings()
        if db_path is None:
            # sqlite+aiosqlite:///./data/appreviewr.db → ./data/appreviewr.db
            raw = settings.database_url.split("///")[-1]
            db_path = Path(raw)
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=settings.cache_ttl_hours)
        self._lock = Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS review_cache (
                        cache_key TEXT PRIMARY KEY,
                        store TEXT NOT NULL,
                        app_id TEXT NOT NULL,
                        country TEXT NOT NULL,
                        language TEXT NOT NULL,
                        sort TEXT NOT NULL,
                        ratings_key TEXT NOT NULL DEFAULT 'all',
                        payload TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                # Older DBs created before ratings_key existed.
                cols = {
                    row["name"]
                    for row in conn.execute("PRAGMA table_info(review_cache)").fetchall()
                }
                if "ratings_key" not in cols:
                    conn.execute(
                        "ALTER TABLE review_cache ADD COLUMN ratings_key TEXT NOT NULL DEFAULT 'all'"
                    )
                conn.commit()

    @staticmethod
    def make_key(
        store: Store,
        app_id: str,
        country: str,
        language: str,
        sort: SortOption | str,
        ratings: list[int] | None = None,
        *,
        ratings_key: str | None = None,
    ) -> str:
        sort_val = sort.value if isinstance(sort, SortOption) else str(sort)
        rk = ratings_key if ratings_key is not None else ratings_cache_key(ratings)
        return (
            f"{store.value}|{app_id}|{country.lower()}|"
            f"{(language or 'en').lower()}|{sort_val}|{rk}"
        )

    def get(
        self,
        store: Store,
        app_id: str,
        country: str,
        language: str,
        sort: SortOption | str,
        ratings: list[int] | None = None,
        *,
        ratings_key: str | None = None,
    ) -> list[Review] | None:
        key = self.make_key(
            store, app_id, country, language, sort, ratings, ratings_key=ratings_key
        )
        with self._lock:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT payload, created_at FROM review_cache WHERE cache_key = ?",
                    (key,),
                ).fetchone()
        if row is None:
            return None
        created = datetime.fromisoformat(row["created_at"])
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - created > self.ttl:
            self.delete_key(key)
            return None
        data = json.loads(row["payload"])
        return [Review.model_validate(item) for item in data]

    def set(
        self,
        store: Store,
        app_id: str,
        country: str,
        language: str,
        sort: SortOption | str,
        reviews: list[Review],
        ratings: list[int] | None = None,
        *,
        ratings_key: str | None = None,
    ) -> None:
        rk = ratings_key if ratings_key is not None else ratings_cache_key(ratings)
        key = self.make_key(
            store, app_id, country, language, sort, ratings, ratings_key=rk
        )
        payload = json.dumps([r.model_dump(mode="json") for r in reviews])
        now = datetime.now(timezone.utc).isoformat()
        sort_val = sort.value if isinstance(sort, SortOption) else str(sort)
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO review_cache
                    (cache_key, store, app_id, country, language, sort, ratings_key,
                     payload, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(cache_key) DO UPDATE SET
                      payload=excluded.payload,
                      ratings_key=excluded.ratings_key,
                      created_at=excluded.created_at
                    """,
                    (
                        key,
                        store.value,
                        app_id,
                        country.lower(),
                        (language or "en").lower(),
                        sort_val,
                        rk,
                        payload,
                        now,
                    ),
                )
                conn.commit()

    def delete_key(self, key: str) -> None:
        with self._lock:
            with self._connect() as conn:
                conn.execute("DELETE FROM review_cache WHERE cache_key = ?", (key,))
                conn.commit()


_cache: ReviewCache | None = None


def get_cache() -> ReviewCache:
    global _cache
    if _cache is None:
        _cache = ReviewCache()
    return _cache


def reset_cache_for_tests(db_path: str | Path) -> ReviewCache:
    global _cache
    _cache = ReviewCache(db_path=db_path)
    return _cache
