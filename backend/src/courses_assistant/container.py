"""Сборка зависимостей приложения (composition root)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from courses_assistant.adapters.broker.redis_streams import RedisStreamsBroker
from courses_assistant.adapters.embeddings.ollama import OllamaEmbedder
from courses_assistant.adapters.llm.gigachat import GigaChatLLM
from courses_assistant.adapters.persistence.database import create_engine, create_session_factory
from courses_assistant.adapters.persistence.unit_of_work import SqlAlchemyUnitOfWork
from courses_assistant.adapters.tokens.jwt import JwtTokenService
from courses_assistant.application.commands import (
    ChangeUserRole,
    CreateChatSession,
    ProcessQuestion,
    RegisterUser,
    RunCronTask,
    SendQuestion,
)
from courses_assistant.application.handlers import Handlers
from courses_assistant.application.message_bus import MessageBus
from courses_assistant.application.ports import (
    LLM,
    Embedder,
    MessageBroker,
    TokenService,
    UnitOfWork,
)
from courses_assistant.config import Settings


@dataclass
class Container:
    settings: Settings
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]
    uow_factory: Callable[[], UnitOfWork]
    llm: LLM
    embedder: Embedder
    broker: MessageBroker
    tokens: TokenService
    handlers: Handlers
    bus: MessageBus

    async def close(self) -> None:
        await self.broker.close()
        await self.engine.dispose()


def build_container(settings: Settings) -> Container:
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)

    def uow_factory() -> UnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory)

    llm = GigaChatLLM(
        credentials=settings.gigachat_credentials,
        scope=settings.gigachat_scope,
        auth_url=settings.gigachat_auth_url,
        base_url=settings.gigachat_base_url,
        model=settings.gigachat_model,
        verify_ssl=settings.gigachat_verify_ssl,
        timeout=settings.llm_timeout,
    )
    embedder = OllamaEmbedder(
        url=settings.ollama_url,
        model=settings.embedding_model,
        dimension=settings.embedding_dimension,
    )
    broker = RedisStreamsBroker(settings.redis_url)

    tokens = JwtTokenService(
        secret=settings.resolved_jwt_secret(),
        algorithm=settings.jwt_algorithm,
        access_ttl=settings.access_token_ttl,
    )

    handlers = Handlers(
        uow_factory=uow_factory,
        llm=llm,
        embedder=embedder,
        broker=broker,
        settings=settings,
    )
    bus = MessageBus(
        {
            CreateChatSession: handlers.create_session,
            SendQuestion: handlers.send_question,
            ProcessQuestion: handlers.process_question,
            RunCronTask: handlers.run_cron_task,
            RegisterUser: handlers.register_user,
            ChangeUserRole: handlers.change_user_role,
        }
    )

    return Container(
        settings=settings,
        engine=engine,
        session_factory=session_factory,
        uow_factory=uow_factory,
        llm=llm,
        embedder=embedder,
        broker=broker,
        tokens=tokens,
        handlers=handlers,
        bus=bus,
    )
