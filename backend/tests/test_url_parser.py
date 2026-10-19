"""URL / ID parser tests."""

import pytest

from app.models import Store
from app.url_parser import ParseError, parse_app_url


@pytest.mark.parametrize(
    "value,store,app_id",
    [
        (
            "https://play.google.com/store/apps/details?id=com.spotify.music",
            Store.GOOGLE_PLAY,
            "com.spotify.music",
        ),
        (
            "play.google.com/store/apps/details?id=com.whatsapp&hl=en&gl=us",
            Store.GOOGLE_PLAY,
            "com.whatsapp",
        ),
        ("com.spotify.music", Store.GOOGLE_PLAY, "com.spotify.music"),
        (
            "https://apps.apple.com/us/app/spotify-music-and-podcasts/id324684580",
            Store.APP_STORE,
            "324684580",
        ),
        (
            "https://itunes.apple.com/app/id310633997",
            Store.APP_STORE,
            "310633997",
        ),
        ("324684580", Store.APP_STORE, "324684580"),
    ],
)
def test_parse_ok(value: str, store: Store, app_id: str) -> None:
    ref = parse_app_url(value)
    assert ref.store == store
    assert ref.app_id == app_id


def test_parse_play_country_lang() -> None:
    ref = parse_app_url(
        "https://play.google.com/store/apps/details?id=com.spotify.music&hl=fr&gl=ca"
    )
    assert ref.language == "fr"
    assert ref.country == "ca"


def test_parse_apple_country() -> None:
    ref = parse_app_url("https://apps.apple.com/gb/app/x/id333903271")
    assert ref.country == "gb"
    assert ref.app_id == "333903271"


def test_reject_other_host() -> None:
    with pytest.raises(ParseError) as ei:
        parse_app_url("https://example.com/app/com.spotify.music")
    assert ei.value.code == "host_not_allowed"


def test_reject_empty() -> None:
    with pytest.raises(ParseError) as ei:
        parse_app_url("  ")
    assert ei.value.code == "empty_input"
