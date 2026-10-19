"""Filter + dedupe unit tests."""

from app.filters import apply_filters, dedupe_reviews, review_matches
from app.models import JobFilters, Review, Store


def _rev(**kwargs) -> Review:
    base = dict(
        store=Store.GOOGLE_PLAY,
        app_id="com.example.app",
        app_name="Example",
        review_id="r1",
        author="A",
        rating=5,
        title=None,
        text="Great app for music",
        date="2024-06-01T12:00:00Z",
        app_version="1.0",
        thumbs_up=1,
        developer_reply=None,
        reply_date=None,
        country="US",
        language="en",
    )
    base.update(kwargs)
    return Review(**base)


def test_keyword_and_rating_filters() -> None:
    reviews = [
        _rev(review_id="1", rating=5, text="Great music"),
        _rev(review_id="2", rating=2, text="Bad music"),
        _rev(review_id="3", rating=5, text="No match"),
    ]
    filters = JobFilters(ratings=[5], keyword="music", max_reviews=100)
    matched = apply_filters(reviews, filters)
    assert [r.review_id for r in matched] == ["1"]


def test_developer_reply_filter() -> None:
    with_reply = _rev(review_id="1", developer_reply="Thanks!")
    without = _rev(review_id="2")
    assert review_matches(with_reply, JobFilters(has_developer_reply=True))
    assert not review_matches(without, JobFilters(has_developer_reply=True))
    assert review_matches(without, JobFilters(has_developer_reply=False))


def test_date_range() -> None:
    review = _rev(date="2024-06-15T00:00:00Z")
    assert review_matches(
        review, JobFilters(date_from="2024-06-01", date_to="2024-06-30T23:59:59Z")
    )
    assert not review_matches(review, JobFilters(date_from="2024-07-01"))


def test_dedupe() -> None:
    a = _rev(review_id="x", country="US")
    b = _rev(review_id="x", country="us")
    c = _rev(review_id="y", country="US")
    out = dedupe_reviews([a, b, c])
    assert len(out) == 2
