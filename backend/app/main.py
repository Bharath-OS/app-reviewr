"""AppReviewr FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.cache import get_cache
from app.config import get_settings
from app.models import ErrorDetail, ErrorResponse, HealthResponse
from app.rate_limit import limiter
from app.routes import app_info, export, health, jobs


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    Path("data").mkdir(parents=True, exist_ok=True)
    get_cache()
    yield
    del settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(app_info.router, prefix="/api")
    app.include_router(jobs.router, prefix="/api")
    app.include_router(export.router, prefix="/api")

    @app.get("/", include_in_schema=False)
    async def root() -> HealthResponse:
        return HealthResponse(service=settings.app_name)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        _request: Request, exc: Exception
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="internal_error",
                    message="An unexpected error occurred.",
                    details={"type": type(exc).__name__} if settings.debug else None,
                )
            ).model_dump(),
        )

    return app


app = create_app()
