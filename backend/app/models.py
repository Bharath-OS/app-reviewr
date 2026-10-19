"""Pydantic models and shared enums for AppReviewr."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Store(str, Enum):
    GOOGLE_PLAY = "google_play"
    APP_STORE = "app_store"


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


# Placeholder shapes used by later milestones (kept for scaffold imports).
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
