"""Создание/обновление пользователя (студента или администратора).

Пример: python -m courses_assistant.scripts.create_user --email s@example.com \
    --password secret --name "Студент"
"""

from __future__ import annotations

import asyncio

import typer
from sqlalchemy import select

from courses_assistant.adapters.persistence.database import (
    create_engine,
    create_session_factory,
)
from courses_assistant.adapters.persistence.orm import UserORM
from courses_assistant.config import get_settings
from courses_assistant.domain.security import hash_password

app = typer.Typer(help="Создание пользователя.")


async def _run(email: str, password: str, name: str, role: str) -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    try:
        async with session_factory() as session:
            existing = (
                await session.execute(
                    select(UserORM).where(UserORM.email == email)
                )
            ).scalar_one_or_none()
            if existing is not None:
                existing.password_hash = hash_password(password)
                existing.name = name
                existing.role = role
                await session.commit()
                typer.echo(f"Обновлён пользователь {email} (id={existing.id}).")
                return
            user = UserORM(
                email=email, name=name, password_hash=hash_password(password), role=role
            )
            session.add(user)
            await session.commit()
            typer.echo(f"Создан пользователь {email} (id={user.id}, role={role}).")
    finally:
        await engine.dispose()


@app.command()
def main(  # noqa: PLR0913
    email: str = typer.Option(..., "--email", "-e"),
    password: str = typer.Option(..., "--password", "-p"),
    name: str = typer.Option("", "--name", "-n"),
    role: str = typer.Option("student", "--role", "-r"),
) -> None:
    asyncio.run(_run(email, password, name or email, role))


if __name__ == "__main__":
    app()
