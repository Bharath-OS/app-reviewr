"""In-memory job orchestration with background fetch, cancel, and SSE fan-out."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

from app.cache import get_cache, ratings_cache_key
from app.config import get_settings
from app.filters import dedupe_reviews, review_matches
from app.models import (
    AppInfo,
    AppRef,
    CreateJobRequest,
    ErrorDetail,
    JobEvent,
    JobFilters,
    JobLimitsNote,
    JobProgress,
    JobResponse,
    JobStatus,
    Review,
    Store,
)
from app.sources import get_source
from app.sources.errors import SourceError
from app.url_parser import ParseError, parse_app_url


def _now() -> datetime:
    return datetime.now(timezone.utc)


class JobRecord:
    def __init__(
        self,
        *,
        job_id: str,
        store: Store,
        app_id: str,
        filters: JobFilters,
        raw_url: str,
    ) -> None:
        self.id = job_id
        self.store = store
        self.app_id = app_id
        self.raw_url = raw_url
        self.filters = filters
        self.status = JobStatus.QUEUED
        self.app_info: AppInfo | None = None
        self.progress = JobProgress(target=filters.max_reviews)
        self.created_at = _now()
        self.updated_at = self.created_at
        self.error: ErrorDetail | None = None
        self.notes: list[JobLimitsNote] = []
        self.reviews: list[Review] = []
        self.cancel_event = asyncio.Event()
        self.subscribers: list[asyncio.Queue[JobEvent | None]] = []
        self.task: asyncio.Task[None] | None = None
        self.force_refresh = False
        self.served_from_cache = False
        self._cache_hits = 0
        self._cache_misses = 0

    def to_response(self) -> JobResponse:
        return JobResponse(
            id=self.id,
            status=self.status,
            store=self.store,
            app_id=self.app_id,
            app_info=self.app_info,
            filters=self.filters,
            progress=self.progress,
            created_at=self.created_at,
            updated_at=self.updated_at,
            error=self.error,
            notes=list(self.notes),
            review_count=len(self.reviews),
            served_from_cache=self.served_from_cache,
            force_refresh=self.force_refresh,
        )


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._lock = asyncio.Lock()

    def would_fully_hit_cache(
        self,
        request: CreateJobRequest,
        *,
        app_ref_language: str | None = None,
    ) -> bool:
        """True if every requested country×ratings batch is already cached (12h TTL)."""
        if request.force_refresh:
            return False
        try:
            app_ref = parse_app_url(request.url)
        except ParseError:
            return False
        settings = get_settings()
        filters = request.filters
        countries = filters.countries[: settings.max_countries_per_job]
        lang = app_ref_language or app_ref.language or (
            filters.languages[0] if filters.languages else "en"
        )
        rk = ratings_cache_key(filters.ratings)
        cache = get_cache()
        for country in countries:
            cached = cache.get(
                app_ref.store,
                app_ref.app_id,
                country,
                lang,
                filters.sort,
                ratings_key=rk,
            )
            if cached is None:
                return False
            # Thin bucket: previous fetch asked for fewer reviews than this job needs.
            if len(cached) < filters.max_reviews:
                return False
        return bool(countries)

    async def create_job(self, request: CreateJobRequest) -> JobRecord:
        settings = get_settings()
        try:
            app_ref = parse_app_url(request.url)
        except ParseError as exc:
            raise ValueError(exc.message) from exc

        filters = request.filters.model_copy(deep=True)
        if len(filters.countries) > settings.max_countries_per_job:
            raise ValueError(
                f"At most {settings.max_countries_per_job} countries per job."
            )
        filters.max_reviews = min(filters.max_reviews, settings.max_reviews_per_job)

        job = JobRecord(
            job_id=uuid.uuid4().hex,
            store=app_ref.store,
            app_id=app_ref.app_id,
            filters=filters,
            raw_url=request.url,
        )
        job.force_refresh = request.force_refresh
        if app_ref.store == Store.APP_STORE:
            job.notes.append(
                JobLimitsNote(
                    code="apple_rss_limit",
                    message=(
                        "App Store Tier 1 uses the public iTunes RSS feed "
                        "(historically ~500 reviews per country). "
                        "If Apple returns an empty feed, results may be zero."
                    ),
                )
            )

        async with self._lock:
            self._jobs[job.id] = job

        job.task = asyncio.create_task(
            self._run_job(
                job,
                app_ref_country=app_ref.country,
                app_ref_language=app_ref.language,
                force_refresh=request.force_refresh,
            )
        )
        return job

    def get(self, job_id: str) -> JobRecord | None:
        return self._jobs.get(job_id)

    async def cancel(self, job_id: str) -> JobRecord | None:
        job = self._jobs.get(job_id)
        if job is None:
            return None
        if job.status in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}:
            return job
        job.cancel_event.set()
        job.status = JobStatus.CANCELLED
        job.progress.message = "Cancelled by user"
        job.updated_at = _now()
        await self._publish(job, JobEvent(type="status", job=job.to_response(), message="cancelled"))
        return job

    async def subscribe(self, job_id: str) -> AsyncIterator[JobEvent]:
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(job_id)
        queue: asyncio.Queue[JobEvent | None] = asyncio.Queue()
        job.subscribers.append(queue)
        # Snapshot first
        await queue.put(JobEvent(type="status", job=job.to_response()))
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield event
                if event.type in {"done", "error"} or (
                    event.job and event.job.status
                    in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}
                ):
                    break
        finally:
            if queue in job.subscribers:
                job.subscribers.remove(queue)

    async def _publish(self, job: JobRecord, event: JobEvent) -> None:
        for queue in list(job.subscribers):
            await queue.put(event)

    async def _run_job(
        self,
        job: JobRecord,
        *,
        app_ref_country: str | None,
        app_ref_language: str | None,
        force_refresh: bool = False,
    ) -> None:
        job.status = JobStatus.RUNNING
        job.updated_at = _now()
        await self._publish(job, JobEvent(type="status", job=job.to_response(), message="started"))

        source = get_source(job.store)
        cache = get_cache()
        settings = get_settings()
        ratings_key = ratings_cache_key(job.filters.ratings)
        try:
            base_ref = AppRef(
                store=job.store,
                app_id=job.app_id,
                country=app_ref_country or job.filters.countries[0],
                language=app_ref_language,
                raw_url=job.raw_url,
            )
            job.app_info = await source.get_app_info(base_ref)
            job.updated_at = _now()
            await self._publish(
                job, JobEvent(type="progress", job=job.to_response(), message="app info loaded")
            )

            collected: list[Review] = []
            per_country_cap = max(1, job.filters.max_reviews)

            for country in job.filters.countries:
                if job.cancel_event.is_set():
                    break
                job.progress.current_country = country.upper()
                job.progress.message = f"Fetching {country.upper()}…"
                job.updated_at = _now()
                await self._publish(job, JobEvent(type="progress", job=job.to_response()))

                lang = app_ref_language or (
                    job.filters.languages[0] if job.filters.languages else "en"
                )
                cached = None
                if not force_refresh:
                    cached = cache.get(
                        job.store,
                        job.app_id,
                        country,
                        lang,
                        job.filters.sort,
                        ratings_key=ratings_key,
                    )
                    # Don't reuse a thinner previous fetch for a larger max_reviews.
                    if cached is not None and len(cached) < job.filters.max_reviews:
                        cached = None
                country_reviews: list[Review]
                if cached is not None:
                    country_reviews = cached
                    job._cache_hits += 1
                    job.progress.message = (
                        f"Cache hit for {country.upper()} "
                        f"(ratings={ratings_key}, no store scrape)"
                    )
                else:
                    job._cache_misses += 1
                    country_reviews = []
                    ref = AppRef(
                        store=job.store,
                        app_id=job.app_id,
                        country=country,
                        language=lang,
                        raw_url=job.raw_url,
                    )
                    app_name = job.app_info.name if job.app_info else job.app_id
                    # Google Play supports per-star scrape (filter_score). Each
                    # star selection gets its own cache bucket — never thin a
                    # mixed "all" cache to satisfy a 1★-only request.
                    # App Store has no star filter API; one pass + post-filter.
                    score_passes: list[int | None]
                    if job.store == Store.GOOGLE_PLAY and job.filters.ratings:
                        score_passes = sorted({int(r) for r in job.filters.ratings})
                    else:
                        score_passes = [None]

                    for score in score_passes:
                        if job.cancel_event.is_set():
                            break
                        if job.progress.matched >= job.filters.max_reviews:
                            break
                        remaining = job.filters.max_reviews - len(
                            dedupe_reviews(collected)
                        )
                        remaining = max(1, remaining)
                        if score is not None:
                            job.progress.message = (
                                f"Fetching {country.upper()} · {score}★…"
                            )
                            job.updated_at = _now()
                            await self._publish(
                                job, JobEvent(type="progress", job=job.to_response())
                            )
                        async for review in source.iter_reviews(
                            ref,
                            sort=job.filters.sort.value,
                            max_reviews=min(
                                remaining, per_country_cap, settings.max_reviews_per_job
                            ),
                            app_name=app_name,
                            filter_score=score,
                        ):
                            if job.cancel_event.is_set():
                                break
                            country_reviews.append(review)
                            job.progress.fetched += 1
                            if review_matches(review, job.filters):
                                collected.append(review)
                                job.progress.matched = len(dedupe_reviews(collected))
                            if job.progress.fetched % 25 == 0:
                                job.updated_at = _now()
                                await self._publish(
                                    job,
                                    JobEvent(type="progress", job=job.to_response()),
                                )
                            if job.progress.matched >= job.filters.max_reviews:
                                break
                    if not job.cancel_event.is_set():
                        cache.set(
                            job.store,
                            job.app_id,
                            country,
                            lang,
                            job.filters.sort,
                            country_reviews,
                            ratings_key=ratings_key,
                        )

                if cached is not None:
                    for review in country_reviews:
                        job.progress.fetched += 1
                        if review_matches(review, job.filters):
                            collected.append(review)
                    job.progress.matched = len(dedupe_reviews(collected))
                    job.updated_at = _now()
                    await self._publish(job, JobEvent(type="progress", job=job.to_response()))

                if job.progress.matched >= job.filters.max_reviews:
                    break

            job.served_from_cache = (
                job._cache_hits > 0 and job._cache_misses == 0 and not force_refresh
            )
            if job.served_from_cache:
                job.notes.append(
                    JobLimitsNote(
                        code="served_from_cache",
                        message=(
                            "Served from AppReviewr cache (12h) for this "
                            "app/country/sort/star-filter. Google/Apple were not "
                            "contacted for review pages. Changing star ratings "
                            "uses a separate cache bucket (or a fresh scrape). "
                            "Use Refresh from store to scrape again."
                        ),
                    )
                )
            elif job._cache_hits and job._cache_misses:
                job.notes.append(
                    JobLimitsNote(
                        code="partial_cache",
                        message=(
                            "Some countries came from cache; others were scraped fresh."
                        ),
                    )
                )

            if job.cancel_event.is_set() or job.status == JobStatus.CANCELLED:
                job.status = JobStatus.CANCELLED
                job.reviews = dedupe_reviews(collected)[: job.filters.max_reviews]
            else:
                job.reviews = dedupe_reviews(collected)[: job.filters.max_reviews]
                job.progress.matched = len(job.reviews)
                job.status = JobStatus.COMPLETED
                job.progress.message = (
                    "Done (from cache)" if job.served_from_cache else "Done"
                )
                if job.store == Store.APP_STORE and not job.reviews:
                    job.notes.append(
                        JobLimitsNote(
                            code="apple_rss_empty",
                            message=(
                                "Apple RSS returned no reviews for the selected "
                                "countries. App preview may still work via lookup."
                            ),
                        )
                    )

            job.updated_at = _now()
            event_type = "done" if job.status == JobStatus.COMPLETED else "status"
            await self._publish(
                job,
                JobEvent(type=event_type, job=job.to_response(), message=job.status.value),
            )
        except SourceError as exc:
            job.status = JobStatus.FAILED
            job.error = ErrorDetail(code=exc.code, message=exc.message)
            job.progress.message = exc.message
            job.updated_at = _now()
            await self._publish(
                job, JobEvent(type="error", job=job.to_response(), message=exc.message)
            )
        except Exception as exc:  # noqa: BLE001
            job.status = JobStatus.FAILED
            job.error = ErrorDetail(code="job_failed", message=str(exc))
            job.progress.message = str(exc)
            job.updated_at = _now()
            await self._publish(
                job, JobEvent(type="error", job=job.to_response(), message=str(exc))
            )
        finally:
            close = getattr(source, "aclose", None)
            if close:
                await close()
            for queue in list(job.subscribers):
                await queue.put(None)


_manager: JobManager | None = None


def get_job_manager() -> JobManager:
    global _manager
    if _manager is None:
        _manager = JobManager()
    return _manager


def reset_job_manager_for_tests() -> JobManager:
    global _manager
    _manager = JobManager()
    return _manager
