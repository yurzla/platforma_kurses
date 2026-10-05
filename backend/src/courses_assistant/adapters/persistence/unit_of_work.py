"""Unit of Work на SQLAlchemy async."""

from __future__ import annotations

from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from courses_assistant.adapters.persistence.repositories import (
    SqlCatalogRepository,
    SqlChatRepository,
    SqlCourseChunkRepository,
    SqlJobRepository,
    SqlUserRepository,
)
from courses_assistant.application.ports import (
    CatalogRepository,
    ChatRepository,
    CourseChunkRepository,
    JobRepository,
    UnitOfWork,
    UserRepository,
)


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self.chat: ChatRepository
        self.chunks: CourseChunkRepository
        self.jobs: JobRepository
        self.users: UserRepository
        self.catalog: CatalogRepository

    async def __aenter__(self) -> SqlAlchemyUnitOfWork:
        self._session = self._session_factory()
        self.chat = SqlChatRepository(self._session)
        self.chunks = SqlCourseChunkRepository(self._session)
        self.jobs = SqlJobRepository(self._session)
        self.users = SqlUserRepository(self._session)
        self.catalog = SqlCatalogRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        assert self._session is not None
        try:
            if exc_type is None:
                await self._session.commit()
            else:
                await self._session.rollback()
        finally:
            await self._session.close()
            self._session = None

    async def commit(self) -> None:
        assert self._session is not None
        await self._session.commit()

    async def rollback(self) -> None:
        assert self._session is not None
        await self._session.rollback()
