"""Factory for Tier 1 review sources."""

from app.models import Store
from app.sources.apple_tier1 import AppleTier1Source
from app.sources.base import ReviewSource
from app.sources.play_tier1 import PlayTier1Source


def get_source(store: Store) -> ReviewSource:
    if store == Store.GOOGLE_PLAY:
        return PlayTier1Source()
    if store == Store.APP_STORE:
        return AppleTier1Source()
    raise ValueError(f"Unsupported store: {store}")
