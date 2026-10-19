"""ReviewSource interface — Tier 1 implementations land in Milestone 2."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from app.models import AppInfo, AppRef, Review


class ReviewSource(ABC):
    """Abstract store adapter. Higher tiers swap in without touching routes."""

    @abstractmethod
    async def get_app_info(self, app_ref: AppRef) -> AppInfo:
        raise NotImplementedError

    @abstractmethod
    def iter_reviews(
        self,
        app_ref: AppRef,
        *,
        sort: str = "newest",
        max_reviews: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[Review]:
        raise NotImplementedError
