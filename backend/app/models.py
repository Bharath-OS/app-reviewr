"""Pydantic models and shared enums for AppReviewr."""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class Store(str, Enum):
    GOOGLE_PLAY = "google_play"
    APP_STORE = "app_store"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SortOption(str, Enum):
    NEWEST = "newest"
    MOST_RELEVANT = "most_relevant"
    RATING = "rating"


class ExportFormat(str, Enum):
    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "AppReviewr"
    version: str = "0.1.0"


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class AppRef(BaseModel):
    store: Store
    app_id: str
    country: str | None = None
    language: str | None = None
    raw_url: str | None = None


class AppInfo(BaseModel):
    store: Store
    app_id: str
    name: str
    developer: str | None = None
    icon_url: str | None = None
    rating: float | None = None
    rating_count: int | None = None
    url: str | None = None


class Review(BaseModel):
    store: Store
    app_id: str
    app_name: str
    review_id: str
    author: str
    rating: int = Field(ge=1, le=5)
    title: str | None = None
    text: str
    date: str
    app_version: str | None = None
    thumbs_up: int | None = None
    developer_reply: str | None = None
    reply_date: str | None = None
    country: str
    language: str | None = None


class JobFilters(BaseModel):
    ratings: list[int] | None = None
    countries: list[str] = Field(default_factory=lambda: ["us"])
    languages: list[str] | None = None
    date_from: str | None = None
    date_to: str | None = None
    keyword: str | None = None
    has_developer_reply: bool | None = None
    sort: SortOption = SortOption.NEWEST
    max_reviews: int = Field(default=200, ge=1, le=2000)

    @field_validator("ratings")
    @classmethod
    def validate_ratings(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return value
        cleaned = sorted({int(v) for v in value if 1 <= int(v) <= 5})
        return cleaned or None

    @field_validator("countries")
    @classmethod
    def validate_countries(cls, value: list[str]) -> list[str]:
        cleaned = [c.strip().lower() for c in value if c and c.strip()]
        if not cleaned:
            return ["us"]
        return cleaned

    @field_validator("languages")
    @classmethod
    def validate_languages(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned = [c.strip().lower() for c in value if c and c.strip()]
        return cleaned or None


class CreateJobRequest(BaseModel):
    url: str = Field(min_length=1)
    filters: JobFilters = Field(default_factory=JobFilters)
    # When true, bypass the 12h review cache and scrape the store again.
    force_refresh: bool = False


class JobProgress(BaseModel):
    fetched: int = 0
    matched: int = 0
    target: int | None = None
    current_country: str | None = None
    message: str | None = None


class JobLimitsNote(BaseModel):
    code: str
    message: str


class JobResponse(BaseModel):
    id: str
    status: JobStatus
    store: Store
    app_id: str
    app_info: AppInfo | None = None
    filters: JobFilters
    progress: JobProgress
    created_at: datetime
    updated_at: datetime
    error: ErrorDetail | None = None
    notes: list[JobLimitsNote] = Field(default_factory=list)
    review_count: int = 0
    # True when every country batch for this job came from the 12h cache (no store scrape).
    served_from_cache: bool = False
    force_refresh: bool = False


class ReviewsPage(BaseModel):
    job_id: str
    total: int
    page: int
    page_size: int
    reviews: list[Review]


class JobEvent(BaseModel):
    type: Literal["progress", "status", "error", "done"]
    job: JobResponse | None = None
    message: str | None = None
