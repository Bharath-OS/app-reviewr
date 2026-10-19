"""Config loading tests."""

from app.config import Settings


def test_default_settings() -> None:
    settings = Settings()
    assert settings.app_name == "AppReviewr"
    assert settings.max_reviews_per_job == 2000
    assert "http://localhost:3741" in settings.cors_origin_list


def test_cors_origin_list_parses() -> None:
    settings = Settings(cors_origins="http://a.test, http://b.test")
    assert settings.cors_origin_list == ["http://a.test", "http://b.test"]
