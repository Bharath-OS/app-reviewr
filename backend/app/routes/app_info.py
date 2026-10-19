"""App preview lookup endpoint."""

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.models import AppInfo, ErrorDetail, ErrorResponse
from app.sources import get_source
from app.sources.errors import SourceError
from app.url_parser import ParseError, parse_app_url

router = APIRouter(tags=["app-info"])


@router.get("/app-info", response_model=AppInfo)
async def get_app_info(url: str = Query(..., min_length=1, description="Store URL or app ID")):
    try:
        app_ref = parse_app_url(url)
    except ParseError as exc:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error=ErrorDetail(code=exc.code, message=exc.message)
            ).model_dump(),
        )

    source = get_source(app_ref.store)
    try:
        return await source.get_app_info(app_ref)
    except SourceError as exc:
        return JSONResponse(
            status_code=exc.status_code or 502,
            content=ErrorResponse(
                error=ErrorDetail(code=exc.code, message=exc.message)
            ).model_dump(),
        )
    finally:
        close = getattr(source, "aclose", None)
        if close:
            await close()
