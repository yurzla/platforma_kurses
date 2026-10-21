
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY backend/pyproject.toml ./backend/pyproject.toml
COPY web/pyproject.toml ./web/pyproject.toml

RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv sync --frozen --no-install-project --no-dev --package courses-assistant

COPY backend/src ./backend/src
COPY backend/alembic.ini ./backend/alembic.ini
COPY backend/alembic ./backend/alembic

RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv sync --frozen --no-dev --package courses-assistant

EXPOSE 5000

CMD ["uvicorn", "courses_assistant.entrypoints.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "5000"]
