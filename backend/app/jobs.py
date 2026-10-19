"""In-memory job orchestration with background fetch, cancel, and SSE fan-out."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

from app.cache import get_cache
from app.config import get_settings
from app.filters import dedupe_reviews, review_matches
from app.models import (
    AppInfo,
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
        )


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._lock = asyncio.Lock()

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

        job.task = asyncio.create_task(self._run_job(job, app_ref_country=app_ref.country, app_ref_language=app_ref.language))
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
    ) -> None:
        from app.models import AppRef

        job.status = JobStatus.RUNNING
        job.updated_at = _now()
        await self._publish(job, JobEvent(type="status", job=job.to_response(), message="started"))

        source = get_source(job.store)
        cache = get_cache()
        settings = get_settings()
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
                cached = cache.get(
                    job.store, job.app_id, country, lang, job.filters.sort
                )
                country_reviews: list[Review]
                if cached is not None:
                    country_reviews = cached
                    job.progress.message = f"Cache hit for {country.upper()}"
                else:
                    country_reviews = []
                    ref = AppRef(
                        store=job.store,
                        app_id=job.app_id,
                        country=country,
                        language=lang,
                        raw_url=job.raw_url,
                    )
                    async for review in source.iter_reviews(
                        ref,
                        sort=job.filters.sort.value,
                        max_reviews=min(per_country_cap, settings.max_reviews_per_job),
                        app_name=job.app_info.name if job.app_info else job.app_id,
                        filter_score=(
                            job.filters.ratings[0]
                            if job.filters.ratings and len(job.filters.ratings) == 1
                            else None
                        ),
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
                                job, JobEvent(type="progress", job=job.to_response())
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

            if job.cancel_event.is_set() or job.status == JobStatus.CANCELLED:
                job.status = JobStatus.CANCELLED
                job.reviews = dedupe_reviews(collected)[: job.filters.max_reviews]
            else:
                job.reviews = dedupe_reviews(collected)[: job.filters.max_reviews]
                job.progress.matched = len(job.reviews)
                job.status = JobStatus.COMPLETED
                job.progress.message = "Done"
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
