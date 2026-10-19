"""Job create / status / events / cancel / reviews endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from app.jobs import get_job_manager
from app.models import (
    CreateJobRequest,
    ErrorDetail,
    ErrorResponse,
    JobResponse,
    ReviewsPage,
)
from app.rate_limit import limiter

router = APIRouter(tags=["jobs"])


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content=ErrorResponse(error=ErrorDetail(code=code, message=message)).model_dump(),
    )


@router.post("/jobs", response_model=JobResponse)
@limiter.limit("10/hour")
async def create_job(request: Request, body: CreateJobRequest) -> JobResponse | JSONResponse:
    manager = get_job_manager()
    try:
        job = await manager.create_job(body)
    except ValueError as exc:
        return _error(400, "invalid_request", str(exc))
    return job.to_response()


@router.get("/jobs/{job_id}", response_model=JobResponse)
@limiter.limit("30/minute")
async def get_job(request: Request, job_id: str) -> JobResponse | JSONResponse:
    job = get_job_manager().get(job_id)
    if job is None:
        return _error(404, "job_not_found", "No job with that id.")
    return job.to_response()


@router.get("/jobs/{job_id}/events", response_model=None)
@limiter.limit("30/minute")
async def job_events(request: Request, job_id: str):
    manager = get_job_manager()
    if manager.get(job_id) is None:
        return _error(404, "job_not_found", "No job with that id.")

    async def event_generator():
        async for event in manager.subscribe(job_id):
            yield {
                "event": event.type,
                "data": event.model_dump_json(),
            }

    return EventSourceResponse(event_generator())


@router.post("/jobs/{job_id}/cancel", response_model=JobResponse)
@limiter.limit("30/minute")
async def cancel_job(request: Request, job_id: str) -> JobResponse | JSONResponse:
    job = await get_job_manager().cancel(job_id)
    if job is None:
        return _error(404, "job_not_found", "No job with that id.")
    return job.to_response()


@router.get("/jobs/{job_id}/reviews", response_model=ReviewsPage)
@limiter.limit("30/minute")
async def list_reviews(
    request: Request,
    job_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> ReviewsPage | JSONResponse:
    job = get_job_manager().get(job_id)
    if job is None:
        return _error(404, "job_not_found", "No job with that id.")
    total = len(job.reviews)
    start = (page - 1) * page_size
    end = start + page_size
    return ReviewsPage(
        job_id=job_id,
        total=total,
        page=page,
        page_size=page_size,
        reviews=job.reviews[start:end],
    )
