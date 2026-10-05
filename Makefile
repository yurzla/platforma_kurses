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
	uv run pytest --cov=courses_assistant --cov-report=term-missing

migrate:
	uv run alembic upgrade head

revision:
	uv run alembic revision --autogenerate -m "$(m)"

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f api worker cron scheduler

build:
	docker build -t courses-assistant:local .
