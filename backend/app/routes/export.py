"""Export endpoint for completed jobs."""

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse, Response

from app.exporters import export_reviews
from app.jobs import get_job_manager
from app.models import ErrorDetail, ErrorResponse, ExportFormat, JobStatus
from app.rate_limit import limiter

router = APIRouter(tags=["export"])


@router.get("/jobs/{job_id}/export", response_model=None)
@limiter.limit("30/minute")
async def export_job(
    request: Request,
    job_id: str,
    format: ExportFormat = Query(ExportFormat.CSV, alias="format"),
):
    job = get_job_manager().get(job_id)
    if job is None:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error=ErrorDetail(code="job_not_found", message="No job with that id.")
            ).model_dump(),
        )
    if job.status not in {JobStatus.COMPLETED, JobStatus.CANCELLED}:
        return JSONResponse(
            status_code=409,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="job_not_ready",
                    message="Wait until the job finishes before exporting.",
                )
            ).model_dump(),
        )

    app_name = job.app_info.name if job.app_info else job.app_id
    body, media_type, filename = export_reviews(
        job.reviews, format, app_name=app_name, store=job.store
    )
    return Response(
        content=body,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-AppReviewr-Count": str(len(job.reviews)),
        },
    )
