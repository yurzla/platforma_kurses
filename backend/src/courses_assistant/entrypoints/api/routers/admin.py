"""Админ-роутер (read-only): статусы job-ов, DLQ, стримы."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from courses_assistant.application.queries import (
    dlq_entries,
    get_job,
    job_status_counts,
    list_jobs,
    stream_overview,
)
from courses_assistant.container import Container
from courses_assistant.domain.models import JobStatus
from courses_assistant.entrypoints.api.dependencies import get_container, require_admin
from courses_assistant.entrypoints.api.schemas import (
    DlqEntry,
    JobListItem,
    JobListResponse,
    JobRead,
    OverviewResponse,
    StreamStat,
)

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


def _stream_targets(container: Container) -> list[tuple[str, str]]:
    s = container.settings
    return [
        (s.stream_requests, s.consumer_group),
        (s.stream_cron, s.cron_group),
        (s.stream_events, s.consumer_group),
        (s.stream_dead, s.consumer_group),
        (s.cron_dlq, s.cron_group),
    ]


@router.get("/overview", response_model=OverviewResponse)
async def overview(container: Container = Depends(get_container)) -> OverviewResponse:
    counts = await job_status_counts(container.uow_factory)
    streams = await stream_overview(container.broker, _stream_targets(container))
    return OverviewResponse(
        status_counts=counts,
        streams=[StreamStat(**stat) for stat in streams],
    )


@router.get("/jobs", response_model=JobListResponse)
async def jobs(
    status: str | None = Query(default=None),
    session_id: int | None = Query(default=None, ge=1),
    search: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    container: Container = Depends(get_container),
) -> JobListResponse:
    parsed_status: JobStatus | None = None
    if status:
        try:
            parsed_status = JobStatus(status)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"Неизвестный статус: {status}") from exc

    items, total = await list_jobs(
        container.uow_factory,
        status=parsed_status,
        session_id=session_id,
        search=search,
        limit=limit,
        offset=offset,
    )
    return JobListResponse(
        items=[
            JobListItem(
                id=job.id,
                session_id=job.session_id,
                status=str(job.status),
                question=job.question,
                attempts=job.attempts,
                error=job.error,
                created_at=job.created_at,
                updated_at=job.updated_at,
            )
            for job in items
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/jobs/{job_id}", response_model=JobRead)
async def job_detail(
    job_id: str,
    container: Container = Depends(get_container),
) -> JobRead:
    job = await get_job(container.uow_factory, job_id)
    return JobRead(
        id=job.id,
        session_id=job.session_id,
        status=str(job.status),
        question=job.question,
        answer=job.answer,
        sources=job.sources,
        rewritten_question=job.rewritten_question,
        error=job.error,
        attempts=job.attempts,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.get("/dlq", response_model=list[DlqEntry])
async def dlq(
    limit: int = Query(default=50, ge=1, le=200),
    container: Container = Depends(get_container),
) -> list[DlqEntry]:
    settings = container.settings
    entries = await dlq_entries(container.broker, settings.stream_dead, limit=limit)
    entries += await dlq_entries(container.broker, settings.cron_dlq, limit=limit)
    return [DlqEntry(**entry) for entry in entries]


@router.get("/streams", response_model=list[StreamStat])
async def streams(container: Container = Depends(get_container)) -> list[StreamStat]:
    stats = await stream_overview(container.broker, _stream_targets(container))
    return [StreamStat(**stat) for stat in stats]
