.PHONY: install lint format typecheck test test-unit test-integration cov migrate revision up down logs build

install:
	uv sync

lint:
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check --fix .

typecheck:
	uv run mypy

test:
	uv run pytest

test-unit:
	uv run pytest -m "not integration"

test-integration:
	uv run pytest -m integration

cov:
	uv run pytest --cov=courses_assistant --cov=courses_web --cov-report=term-missing

migrate:
	uv run alembic -c backend/alembic.ini upgrade head

revision:
	uv run alembic -c backend/alembic.ini revision --autogenerate -m "$(m)"

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f api web worker cron scheduler

build:
	docker build -f backend/Dockerfile -t courses-assistant:local .
	docker build -f web/Dockerfile -t courses-web:local .
