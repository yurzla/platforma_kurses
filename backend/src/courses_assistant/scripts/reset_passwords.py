"""Генерация новых паролей для всех пользователей.

Пароли шифруются ключом PASSWORD_KEY из .env, а логины и сами пароли
записываются в отдельный файл вне git.

Пример:
    uv run python -m courses_assistant.scripts.reset_passwords \
        --file .secrets/passwords.txt
"""

from __future__ import annotations

import asyncio
import os
import secrets
import tempfile
from pathlib import Path

import typer
from sqlalchemy import delete, select

from courses_assistant.adapters.persistence.database import (
    create_engine,
    create_session_factory,
)
from courses_assistant.adapters.persistence.orm import RefreshTokenORM, UserORM
from courses_assistant.config import get_settings
from courses_assistant.domain.security import encrypt_password

app = typer.Typer(help="Сброс паролей всех пользователей.")

DEFAULT_FILE = Path(".secrets/passwords.txt")


def _write_credentials(path: Path, credentials: list[tuple[str, str]]) -> None:
    """Атомарно пишет файл с логинами и паролями, доступный только владельцу."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=".passwords-", text=True)
    tmp_path = Path(tmp_name)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write("# Сгенерированные пароли. Файл не коммитить.\n")
            for email, password in credentials:
                handle.write(f"{email}\t{password}\n")
        os.replace(tmp_path, path)
        os.chmod(path, 0o600)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


async def _run(path: Path) -> int:
    settings = get_settings()
    try:
        password_key = settings.require_password_key()
    except ValueError as exc:
        typer.echo(f"Ошибка: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    try:
        async with session_factory() as session:
            users = (
                (await session.execute(select(UserORM).order_by(UserORM.id)))
                .scalars()
                .all()
            )
            credentials: list[tuple[str, str]] = []
            for user in users:
                password = secrets.token_urlsafe(12)
                user.password_hash = encrypt_password(password, password_key)
                credentials.append((user.email, password))
            await session.execute(delete(RefreshTokenORM))
            _write_credentials(path, credentials)
            await session.commit()
    finally:
        await engine.dispose()
    return len(credentials)


@app.command()
def main(file: Path = typer.Option(DEFAULT_FILE, "--file", "-f")) -> None:
    count = asyncio.run(_run(file))
    typer.echo(f"Обновлены пароли пользователей: {count}. Файл: {file}")


if __name__ == "__main__":
    app()
