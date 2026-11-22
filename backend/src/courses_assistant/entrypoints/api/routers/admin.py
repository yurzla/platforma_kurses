"""Админ-роутер (read-only): статусы job-ов, DLQ, стримы."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, or_, select, text, update

from courses_assistant.adapters.embeddings.ollama import check_ollama_model
from courses_assistant.adapters.persistence.orm import (
    ChatMessageORM,
    ChatSessionORM,
    ChoiceQuestionMetadataORM,
    ChunkEmbeddingORM,
    ContentChunkORM,
    CourseORM,
    EnrollmentORM,
    JobORM,
    LessonORM,
    RefreshTokenORM,
    SectionORM,
    StepChoiceOptionORM,
    StepContentORM,
    StepORM,
    StepSourceORM,
    UserCourseWishlistORM,
    UserLearningPreferencesORM,
    UserORM,
    UserStepProgressORM,
)
from courses_assistant.application.commands import ChangeUserRole
from courses_assistant.application.queries import (
    dlq_entries,
    get_job,
    job_status_counts,
    list_jobs,
    stream_overview,
)
from courses_assistant.container import Container
from courses_assistant.domain.errors import CannotChangeOwnRole, InvalidRole, UserNotFound
from courses_assistant.domain.models import USER_ROLES, JobStatus, User
from courses_assistant.domain.security import encrypt_password
from courses_assistant.entrypoints.api.dependencies import (
    get_container,
    require_admin,
)
from courses_assistant.entrypoints.api.schemas import (
    AdminCourseListItem,
    AdminCourseListResponse,
    AdminCourseUpdate,
    AdminHealth,
    AdminUserCreate,
    AdminUserUpdate,
    ChunkDetail,
    ChunkListItem,
    ChunkListResponse,
    DlqEntry,
    IndexCourseSummary,
    IndexQueueState,
    IndexSummary,
    JobListItem,
    JobListResponse,
    JobRead,
    JobTimeline,
    OverviewResponse,
    RetrievalSettings,
    StreamStat,
    UserListItem,
    UserListResponse,
    WorkerLiveness,
)

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)

logger = structlog.get_logger(__name__)


async def _admin_course_item(session, course: CourseORM) -> AdminCourseListItem:
    lessons = await session.scalar(
        select(func.count())
        .select_from(LessonORM)
        .join(SectionORM)
        .where(SectionORM.course_id == course.id)
    )
    steps = await session.scalar(
        select(func.count())
        .select_from(StepORM)
        .join(LessonORM)
        .join(SectionORM)
        .where(SectionORM.course_id == course.id)
    )
    students = await session.scalar(
        select(func.count()).select_from(EnrollmentORM).where(EnrollmentORM.course_id == course.id)
    )
    owner = await session.get(UserORM, course.owner_id) if course.owner_id is not None else None
    return AdminCourseListItem(
        id=course.id,
        title=course.title,
        is_published=course.is_published,
        owner_id=course.owner_id,
        owner_name=owner.name if owner else None,
        lessons_count=int(lessons or 0),
        steps_count=int(steps or 0),
        students_count=int(students or 0),
    )


async def _delete_course_tree(session, course_id: int) -> None:
    section_ids = list(
        (
            await session.execute(select(SectionORM.id).where(SectionORM.course_id == course_id))
        ).scalars()
    )
    lesson_ids = (
        []
        if not section_ids
        else list(
            (
                await session.execute(
                    select(LessonORM.id).where(LessonORM.section_id.in_(section_ids))
                )
            ).scalars()
        )
    )
    step_ids = (
        []
        if not lesson_ids
        else list(
            (
                await session.execute(select(StepORM.id).where(StepORM.lesson_id.in_(lesson_ids)))
            ).scalars()
        )
    )
    chunk_filter = [ContentChunkORM.course_id == course_id]
    if lesson_ids:
        chunk_filter.append(ContentChunkORM.lesson_id.in_(lesson_ids))
    if step_ids:
        chunk_filter.append(ContentChunkORM.step_id.in_(step_ids))
    chunk_ids = list(
        (await session.execute(select(ContentChunkORM.id).where(or_(*chunk_filter)))).scalars()
    )
    if chunk_ids:
        await session.execute(
            delete(ChunkEmbeddingORM).where(ChunkEmbeddingORM.chunk_id.in_(chunk_ids))
        )
    await session.execute(delete(ContentChunkORM).where(or_(*chunk_filter)))
    session_ids = list(
        (
            await session.execute(
                select(ChatSessionORM.id).where(ChatSessionORM.course_id == course_id)
            )
        ).scalars()
    )
    if session_ids:
        await session.execute(delete(JobORM).where(JobORM.session_id.in_(session_ids)))
        await session.execute(
            delete(ChatMessageORM).where(ChatMessageORM.session_id.in_(session_ids))
        )
        await session.execute(delete(ChatSessionORM).where(ChatSessionORM.id.in_(session_ids)))
    await session.execute(delete(EnrollmentORM).where(EnrollmentORM.course_id == course_id))
    await session.execute(
        delete(UserCourseWishlistORM).where(UserCourseWishlistORM.course_id == course_id)
    )
    if step_ids:
        await session.execute(
            delete(UserStepProgressORM).where(UserStepProgressORM.step_id.in_(step_ids))
        )
        await session.execute(
            delete(StepChoiceOptionORM).where(StepChoiceOptionORM.step_id.in_(step_ids))
        )
        await session.execute(
            delete(ChoiceQuestionMetadataORM).where(ChoiceQuestionMetadataORM.step_id.in_(step_ids))
        )
        await session.execute(delete(StepSourceORM).where(StepSourceORM.step_id.in_(step_ids)))
        await session.execute(delete(StepContentORM).where(StepContentORM.step_id.in_(step_ids)))
        await session.execute(delete(StepORM).where(StepORM.id.in_(step_ids)))
    if lesson_ids:
        await session.execute(delete(LessonORM).where(LessonORM.id.in_(lesson_ids)))
    if section_ids:
        await session.execute(delete(SectionORM).where(SectionORM.id.in_(section_ids)))
    await session.execute(delete(CourseORM).where(CourseORM.id == course_id))


def _stream_targets(container: Container) -> list[tuple[str, str, str]]:
    s = container.settings
    return [
        (s.stream_requests, s.consumer_group, "processing"),
        (s.stream_index, s.index_group, "processing"),
        (s.stream_cron, s.cron_group, "processing"),
        (s.stream_events, s.consumer_group, "processing"),
        (s.stream_dead, s.consumer_group, "dead"),
        (s.index_dlq, s.index_group, "dead"),
        (s.cron_dlq, s.cron_group, "dead"),
    ]


def _message_order(message_id: str) -> int:
    """Порядок по времени сообщения из Redis Streams id (<ms>-<seq>)."""
    prefix = message_id.split("-", 1)[0]
    return int(prefix) if prefix.isdigit() else 0


def _embedding_model_subquery():
    return (
        select(ChunkEmbeddingORM.model_name)
        .where(ChunkEmbeddingORM.chunk_id == ContentChunkORM.id)
        .order_by(ChunkEmbeddingORM.id.desc())
        .limit(1)
        .correlate(ContentChunkORM)
        .scalar_subquery()
        .label("model_name")
    )


def _chunk_conditions(
    course_id: int | None,
    source_type: str | None,
    search: str | None,
) -> list:
    conditions = []
    if course_id is not None:
        conditions.append(ContentChunkORM.course_id == course_id)
    if source_type:
        conditions.append(ContentChunkORM.source_type == source_type.strip())
    if search and search.strip():
        conditions.append(ContentChunkORM.chunk_text.ilike(f"%{search.strip()}%"))
    return conditions


def _chunk_item(
    chunk: ContentChunkORM,
    course_title: str | None,
    lesson_title: str | None,
    model_name: str | None,
) -> ChunkListItem:
    return ChunkListItem(
        id=chunk.id,
        course_id=chunk.course_id,
        course_title=course_title,
        lesson_id=chunk.lesson_id,
        lesson_title=lesson_title,
        step_id=chunk.step_id,
        chunk_index=chunk.chunk_index,
        source_type=chunk.source_type,
        preview=chunk.chunk_text[:240],
        has_embedding=model_name is not None,
        model_name=model_name,
        created_at=chunk.created_at,
    )


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
    stream: str | None = Query(default=None, max_length=100),
    container: Container = Depends(get_container),
) -> list[DlqEntry]:
    settings = container.settings
    dead_streams = [settings.stream_dead, settings.index_dlq, settings.cron_dlq]
    if stream:
        dead_streams = [dead for dead in dead_streams if dead == stream]
    entries: list[dict] = []
    for dead_stream in dead_streams:
        for entry in await dlq_entries(container.broker, dead_stream, limit=limit):
            entries.append({"dead_stream": dead_stream, **entry})
    entries.sort(key=lambda entry: _message_order(str(entry.get("message_id", ""))), reverse=True)
    return [DlqEntry(**entry) for entry in entries[:limit]]


@router.get("/streams", response_model=list[StreamStat])
async def streams(container: Container = Depends(get_container)) -> list[StreamStat]:
    stats = await stream_overview(container.broker, _stream_targets(container))
    return [StreamStat(**stat) for stat in stats]


@router.get("/chunks", response_model=ChunkListResponse)
async def chunks(
    course_id: int | None = Query(default=None, ge=1),
    source_type: str | None = Query(default=None, max_length=50),
    search: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    container: Container = Depends(get_container),
) -> ChunkListResponse:
    conditions = _chunk_conditions(course_id, source_type, search)
    model_name = _embedding_model_subquery()
    async with container.session_factory() as session:
        statement = (
            select(
                ContentChunkORM,
                CourseORM.title.label("course_title"),
                LessonORM.title.label("lesson_title"),
                model_name,
            )
            .outerjoin(CourseORM, CourseORM.id == ContentChunkORM.course_id)
            .outerjoin(LessonORM, LessonORM.id == ContentChunkORM.lesson_id)
            .where(*conditions)
            .order_by(ContentChunkORM.id)
            .limit(limit)
            .offset(offset)
        )
        rows = (await session.execute(statement)).all()
        total = await session.scalar(
            select(func.count()).select_from(ContentChunkORM).where(*conditions)
        )
    return ChunkListResponse(
        items=[
            _chunk_item(chunk, course_title, lesson_title, chunk_model)
            for chunk, course_title, lesson_title, chunk_model in rows
        ],
        total=int(total or 0),
        limit=limit,
        offset=offset,
    )


@router.get("/chunks/{chunk_id}", response_model=ChunkDetail)
async def chunk_detail(
    chunk_id: int,
    container: Container = Depends(get_container),
) -> ChunkDetail:
    async with container.session_factory() as session:
        chunk = await session.get(ContentChunkORM, chunk_id)
        if chunk is None:
            raise HTTPException(status_code=404, detail="Чанк не найден")
        course_title = None
        if chunk.course_id is not None:
            course_title = await session.scalar(
                select(CourseORM.title).where(CourseORM.id == chunk.course_id)
            )
        lesson_title = None
        if chunk.lesson_id is not None:
            lesson_title = await session.scalar(
                select(LessonORM.title).where(LessonORM.id == chunk.lesson_id)
            )
        embedding = (
            await session.execute(
                select(ChunkEmbeddingORM)
                .where(ChunkEmbeddingORM.chunk_id == chunk.id)
                .order_by(ChunkEmbeddingORM.id.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
    item = _chunk_item(
        chunk, course_title, lesson_title, embedding.model_name if embedding else None
    )
    return ChunkDetail(
        **item.model_dump(),
        chunk_text=chunk.chunk_text,
        embedding_dimension=(
            len(embedding.embedding) if embedding and embedding.embedding else None
        ),
        embedding_created_at=embedding.created_at if embedding else None,
    )


@router.get("/index", response_model=IndexSummary)
async def index_summary(container: Container = Depends(get_container)) -> IndexSummary:
    settings = container.settings
    async with container.session_factory() as session:
        total_chunks = await session.scalar(select(func.count()).select_from(ContentChunkORM))
        total_embeddings = await session.scalar(select(func.count()).select_from(ChunkEmbeddingORM))
        chunks_without_embedding = await session.scalar(
            select(func.count())
            .select_from(ContentChunkORM)
            .where(
                ~select(ChunkEmbeddingORM.id)
                .where(ChunkEmbeddingORM.chunk_id == ContentChunkORM.id)
                .exists()
            )
        )
        type_rows = (
            await session.execute(
                select(ContentChunkORM.source_type, func.count()).group_by(
                    ContentChunkORM.source_type
                )
            )
        ).all()
        last_embedding_at = await session.scalar(select(func.max(ChunkEmbeddingORM.created_at)))

        chunk_rows = (
            await session.execute(
                select(
                    ContentChunkORM.course_id.label("course_id"),
                    func.count(ContentChunkORM.id).label("chunks"),
                    func.count(ContentChunkORM.id)
                    .filter(ContentChunkORM.source_type == "course_description")
                    .label("description_chunks"),
                    func.count(ContentChunkORM.id)
                    .filter(ContentChunkORM.source_type != "course_description")
                    .label("step_chunks"),
                )
                .where(ContentChunkORM.course_id.is_not(None))
                .group_by(ContentChunkORM.course_id)
            )
        ).all()
        chunk_by_course: dict[int, tuple[int, int, int]] = {}
        for row in chunk_rows:
            if row.course_id is None:
                continue
            chunk_by_course[int(row.course_id)] = (
                int(row.chunks),
                int(row.description_chunks),
                int(row.step_chunks),
            )
        embedding_rows = (
            await session.execute(
                select(ContentChunkORM.course_id, func.count(ChunkEmbeddingORM.id))
                .join(ChunkEmbeddingORM, ChunkEmbeddingORM.chunk_id == ContentChunkORM.id)
                .where(ContentChunkORM.course_id.is_not(None))
                .group_by(ContentChunkORM.course_id)
            )
        ).all()
        embedding_by_course: dict[int, int] = {}
        for course_id, count in embedding_rows:
            if course_id is not None:
                embedding_by_course[int(course_id)] = int(count)
        course_rows = (
            await session.execute(select(CourseORM.id, CourseORM.title).order_by(CourseORM.id))
        ).all()

    queue = IndexQueueState()
    try:
        if await container.broker.ping():
            queue_stats = await container.broker.stream_stats(
                settings.stream_index, settings.index_group
            )
            dead_stats = await container.broker.stream_stats(
                settings.index_dlq, settings.index_group
            )
            queue = IndexQueueState(
                exists=bool(queue_stats.get("exists")),
                length=int(queue_stats.get("length") or 0),
                pending=queue_stats.get("pending"),
                lag=queue_stats.get("lag"),
                queue_size=int(queue_stats.get("pending") or 0)
                + int(queue_stats.get("lag") or 0),
                consumers=queue_stats.get("consumers"),
                dead_letters=int(dead_stats.get("length") or 0),
                available=True,
            )
        else:
            queue = IndexQueueState(available=False)
    except Exception as exc:  # noqa: BLE001
        logger.warning("index_queue_stats_failed", error=str(exc))
        queue = IndexQueueState(available=False)

    courses: list[IndexCourseSummary] = []
    for raw_course_id, title in course_rows:
        course_id = int(raw_course_id)
        chunk_count, description_chunks, step_chunks = chunk_by_course.get(
            course_id, (0, 0, 0)
        )
        embeddings = embedding_by_course.get(course_id, 0)
        without_embedding = max(0, chunk_count - embeddings)
        if chunk_count == 0:
            status = "empty"
        elif embeddings == 0:
            status = "missing_embeddings"
        elif without_embedding > 0:
            status = "partial"
        else:
            status = "ok"
        courses.append(
            IndexCourseSummary(
                id=course_id,
                title=title,
                chunks=chunk_count,
                description_chunks=description_chunks,
                step_chunks=step_chunks,
                embeddings=embeddings,
                without_embedding=without_embedding,
                status=status,
            )
        )
    status_order = {"empty": 0, "missing_embeddings": 1, "partial": 2, "ok": 3}
    courses.sort(key=lambda course: (status_order.get(course.status, 4), -course.chunks, course.id))
    return IndexSummary(
        total_chunks=int(total_chunks or 0),
        total_embeddings=int(total_embeddings or 0),
        chunks_without_embedding=int(chunks_without_embedding or 0),
        courses_without_embeddings=sum(1 for course in courses if course.embeddings == 0),
        courses_without_chunks=sum(1 for course in courses if course.chunks == 0),
        by_source_type={source_type: int(count) for source_type, count in type_rows},
        model_name=settings.embedding_model,
        dimension=settings.embedding_dimension,
        last_embedding_at=last_embedding_at,
        queue=queue,
        courses=courses,
    )


@router.get("/health", response_model=AdminHealth)
async def admin_health(container: Container = Depends(get_container)) -> AdminHealth:
    settings = container.settings
    dependencies: dict[str, str] = {}

    if container.engine is not None:
        try:
            async with container.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            dependencies["postgres"] = "ok"
        except Exception as exc:  # noqa: BLE001
            dependencies["postgres"] = f"unavailable: {exc}"
    else:
        dependencies["postgres"] = "unavailable"

    dependencies["redis"] = "ok" if await container.broker.ping() else "unavailable"

    ollama_available, ollama_error = await check_ollama_model(
        settings.ollama_url, settings.embedding_model
    )
    dependencies["ollama"] = (
        "ok" if ollama_available else f"unavailable: {ollama_error or 'нет ответа'}"
    )

    timeline = JobTimeline()
    if container.session_factory is not None:
        async with container.session_factory() as session:
            row = (
                await session.execute(
                    select(
                        func.max(JobORM.updated_at).filter(JobORM.status == "done"),
                        func.max(JobORM.updated_at).filter(JobORM.status == "failed"),
                        func.min(JobORM.created_at).filter(JobORM.status == "queued"),
                    )
                )
            ).one()
            timeline = JobTimeline(
                last_done_at=row[0],
                last_failed_at=row[1],
                oldest_queued_at=row[2],
            )

    workers: list[WorkerLiveness] = []
    redis_available = await container.broker.ping()
    for name, stream, group in (
        ("chat", settings.stream_requests, settings.consumer_group),
        ("indexer", settings.stream_index, settings.index_group),
        ("cron", settings.stream_cron, settings.cron_group),
    ):
        consumers: int | None = None
        if redis_available:
            try:
                stats = await container.broker.stream_stats(stream, group)
                consumers = stats.get("consumers")
            except Exception as exc:  # noqa: BLE001
                logger.warning("worker_liveness_failed", group=group, error=str(exc))
        workers.append(
            WorkerLiveness(
                name=name,
                stream=stream,
                group=group,
                consumers=consumers,
                available=bool(consumers),
            )
        )

    return AdminHealth(
        status="ok" if all(value == "ok" for value in dependencies.values()) else "degraded",
        dependencies=dependencies,
        ollama_model=settings.embedding_model,
        ollama_model_available=ollama_available,
        jobs=timeline,
        workers=workers,
        settings=RetrievalSettings(
            embedding_model=settings.embedding_model,
            embedding_dimension=settings.embedding_dimension,
            retrieval_top_k=settings.retrieval_top_k,
        ),
    )


@router.get("/users", response_model=UserListResponse)
async def users(
    search: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    container: Container = Depends(get_container),
) -> UserListResponse:
    async with container.uow_factory() as uow:
        items = await uow.users.list(search=search, limit=limit, offset=offset)
        total = await uow.users.count(search=search)
    return UserListResponse(
        items=[_user_item(user) for user in items],
        total=total,
        limit=limit,
        offset=offset,
    )


def _user_item(user: User | UserORM) -> UserListItem:
    return UserListItem(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        # Репозиторий списка пользователей возвращает доменную модель без даты,
        # а SQLAlchemy-модель используется в административных изменениях.
        created_at=getattr(user, "created_at", None),
    )


async def _ensure_unique_email(session, email: str, user_id: int | None = None) -> None:
    statement = select(UserORM.id).where(UserORM.email == email)
    if user_id is not None:
        statement = statement.where(UserORM.id != user_id)
    if await session.scalar(statement) is not None:
        raise HTTPException(status_code=409, detail="Этот email уже зарегистрирован")


@router.post("/users", response_model=UserListItem, status_code=201)
async def create_user(
    payload: AdminUserCreate,
    container: Container = Depends(get_container),
) -> UserListItem:
    if payload.role not in USER_ROLES:
        raise HTTPException(status_code=422, detail="Неизвестная роль пользователя")
    async with container.session_factory() as session:
        await _ensure_unique_email(session, payload.email)
        user = UserORM(
            email=payload.email,
            name=payload.name,
            password_hash=encrypt_password(
                payload.password, container.settings.require_password_key()
            ),
            role=payload.role,
        )
        session.add(user)
        await session.flush()
        result = _user_item(user)
        await session.commit()
        return result


@router.patch("/users/{user_id}", response_model=UserListItem)
async def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    actor: User = Depends(require_admin),
    container: Container = Depends(get_container),
) -> UserListItem:
    # Сохраняем отдельный путь смены роли: он используется прикладным слоем и
    # защищает от изменения собственной роли. Также это делает старый API
    # совместимым с существующими клиентами.
    if payload.model_fields_set == {"role"}:
        if actor.id == user_id and payload.role == actor.role:
            return _user_item(actor)
        try:
            user = await container.handlers.change_user_role(
                ChangeUserRole(actor_id=actor.id, user_id=user_id, role=payload.role or "")
            )
        except InvalidRole as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except CannotChangeOwnRole as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except UserNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return _user_item(user)
    async with container.session_factory() as session:
        orm_user = await session.get(UserORM, user_id)
        if orm_user is None:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        if payload.role is not None:
            if payload.role not in USER_ROLES:
                raise HTTPException(status_code=422, detail="Неизвестная роль пользователя")
            if actor.id == user_id and payload.role != orm_user.role:
                raise HTTPException(status_code=403, detail="Нельзя менять собственную роль")
            orm_user.role = payload.role
        if payload.email is not None:
            await _ensure_unique_email(session, payload.email, user_id)
            orm_user.email = payload.email
        if payload.name is not None:
            orm_user.name = payload.name
        if payload.password is not None:
            orm_user.password_hash = encrypt_password(
                payload.password, container.settings.require_password_key()
            )
        result = _user_item(orm_user)
        await session.commit()
        return result


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    actor: User = Depends(require_admin),
    container: Container = Depends(get_container),
) -> None:
    if actor.id == user_id:
        raise HTTPException(status_code=403, detail="Нельзя удалить собственную учётную запись")
    async with container.session_factory() as session:
        if await session.get(UserORM, user_id) is None:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        session_ids = list(
            (
                await session.execute(
                    select(ChatSessionORM.id).where(ChatSessionORM.user_id == user_id)
                )
            ).scalars()
        )
        if session_ids:
            await session.execute(delete(JobORM).where(JobORM.session_id.in_(session_ids)))
            await session.execute(
                delete(ChatMessageORM).where(ChatMessageORM.session_id.in_(session_ids))
            )
            await session.execute(delete(ChatSessionORM).where(ChatSessionORM.id.in_(session_ids)))
        await session.execute(delete(RefreshTokenORM).where(RefreshTokenORM.user_id == user_id))
        await session.execute(
            delete(UserLearningPreferencesORM).where(UserLearningPreferencesORM.user_id == user_id)
        )
        await session.execute(
            delete(UserCourseWishlistORM).where(UserCourseWishlistORM.user_id == user_id)
        )
        await session.execute(
            delete(UserStepProgressORM).where(UserStepProgressORM.user_id == user_id)
        )
        await session.execute(delete(EnrollmentORM).where(EnrollmentORM.user_id == user_id))
        # Курсы преподавателя сохраняются, но становятся курсами платформы.
        await session.execute(
            update(CourseORM).where(CourseORM.owner_id == user_id).values(owner_id=None)
        )
        await session.execute(delete(UserORM).where(UserORM.id == user_id))
        await session.commit()


@router.get("/courses", response_model=AdminCourseListResponse)
async def courses(
    search: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    container: Container = Depends(get_container),
) -> AdminCourseListResponse:
    async with container.session_factory() as session:
        conditions = []
        if search:
            conditions.append(CourseORM.title.ilike(f"%{search.strip()}%"))
        statement = (
            select(CourseORM).where(*conditions).order_by(CourseORM.id).limit(limit).offset(offset)
        )
        rows = (await session.execute(statement)).scalars().all()
        total = await session.scalar(select(func.count()).select_from(CourseORM).where(*conditions))
        return AdminCourseListResponse(
            items=[await _admin_course_item(session, course) for course in rows],
            total=int(total or 0),
            limit=limit,
            offset=offset,
        )


@router.patch("/courses/{course_id}", response_model=AdminCourseListItem)
async def update_course(
    course_id: int,
    payload: AdminCourseUpdate,
    container: Container = Depends(get_container),
) -> AdminCourseListItem:
    async with container.session_factory() as session:
        course = await session.get(CourseORM, course_id)
        if course is None:
            raise HTTPException(status_code=404, detail="Курс не найден")
        if "owner_id" in payload.model_fields_set:
            if payload.owner_id is not None:
                owner = await session.get(UserORM, payload.owner_id)
                if owner is None or owner.role != "teacher":
                    raise HTTPException(
                        status_code=422, detail="Автором может быть только преподаватель"
                    )
            course.owner_id = payload.owner_id
        if "is_published" in payload.model_fields_set:
            course.is_published = bool(payload.is_published)
        result = await _admin_course_item(session, course)
        await session.commit()
        return result


@router.delete("/courses/{course_id}", status_code=204)
async def delete_course(
    course_id: int,
    container: Container = Depends(get_container),
) -> None:
    async with container.session_factory() as session:
        if await session.get(CourseORM, course_id) is None:
            raise HTTPException(status_code=404, detail="Курс не найден")
        await _delete_course_tree(session, course_id)
        await session.commit()
