"""Shared pytest fixtures."""

import os

import pytest
from fastapi.testclient import TestClient

# Disable rate limits for unit/API tests before app import side effects.
os.environ["APPREVIEW_DISABLE_RATE_LIMIT"] = "1"

from app.cache import reset_cache_for_tests  # noqa: E402
from app.jobs import reset_job_manager_for_tests  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture
def client(tmp_path) -> TestClient:
    reset_job_manager_for_tests()
    reset_cache_for_tests(tmp_path / "test-cache.db")
    # Recreate limiter enabled flag is already set via env before import;
    # rebuild app each test for isolation.
    app = create_app()
    with TestClient(app) as c:
        yield c
