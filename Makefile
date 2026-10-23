# FlexTravel Planner — developer shortcuts
# Usage: make <target>. Requires Docker (e.g. OrbStack) and uv.

.PHONY: db-up db-down db-reset migrate dev test lint format

## Start Postgres + PostGIS and wait until it accepts connections
db-up:
	docker compose up -d --wait db

## Stop the database (data is kept in a Docker volume)
db-down:
	docker compose down

## Delete the database volume and start fresh
db-reset:
	docker compose down -v
	docker compose up -d --wait db

## Apply database migrations to the development database
migrate:
	cd backend && uv run alembic upgrade head

## Run the API with auto-reload on http://127.0.0.1:8000 (docs at /docs)
dev:
	cd backend && uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

## Run the backend tests (needs `make db-up`)
test:
	cd backend && uv run pytest

## Check linting and formatting
lint:
	cd backend && uv run ruff check . && uv run ruff format --check .

## Fix lint issues and format code
format:
	cd backend && uv run ruff check --fix . && uv run ruff format .
