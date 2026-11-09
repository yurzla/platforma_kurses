"""Админ-роутер (read-only): статусы job-ов, DLQ, стримы."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, or_, select, update

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
from courses_assistant.domain.security import hash_password
from courses_assistant.entrypoints.api.dependencies import (
    get_container,
    require_admin,
)
from courses_assistant.entrypoints.api.schemas import (
    AdminCourseListItem,
    AdminCourseListResponse,
    AdminCourseUpdate,
    AdminUserCreate,
    AdminUserUpdate,
    DlqEntry,
    JobListItem,
    JobListResponse,
    JobRead,
    OverviewResponse,
    StreamStat,
    UserListItem,
    UserListResponse,
)

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


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
            password_hash=hash_password(payload.password),
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
            orm_user.password_hash = hash_password(payload.password)
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
