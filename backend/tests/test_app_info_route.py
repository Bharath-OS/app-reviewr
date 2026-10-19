"""GET /api/app-info route tests."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.models import AppInfo, Store


def test_app_info_bad_url(client: TestClient) -> None:
    response = client.get("/api/app-info", params={"url": "https://evil.example/app"})
    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "host_not_allowed"


def test_app_info_ok(client: TestClient) -> None:
    fake = AppInfo(
        store=Store.GOOGLE_PLAY,
        app_id="com.spotify.music",
        name="Spotify",
        developer="Spotify AB",
        icon_url="https://example.com/icon.png",
        rating=4.5,
        rating_count=1000,
        url="https://play.google.com/store/apps/details?id=com.spotify.music",
    )
    with patch("app.routes.app_info.get_source") as get_source:
        source = AsyncMock()
        source.get_app_info = AsyncMock(return_value=fake)
        source.aclose = AsyncMock()
        get_source.return_value = source
        response = client.get(
            "/api/app-info",
            params={"url": "https://play.google.com/store/apps/details?id=com.spotify.music"},
        )
    assert response.status_code == 200
    assert response.json()["name"] == "Spotify"
