# FlexTravel Planner — developer shortcuts
# Usage: make <target>. Requires Docker (e.g. OrbStack), uv and Node.js.

.PHONY: install data dev dev-api dev-web db-up db-down db-reset migrate test test-web e2e lint format

## Install backend and frontend dependencies
install:
	cd backend && uv sync
	cd frontend && npm ci --no-fund --no-audit

## Prepare map, bus and station data and build the route planner's graph (~2 min)
data:
	@scripts/prepare_data.sh

## Start everything (database, API, web app) in one terminal; Ctrl+C stops it
dev:
	@scripts/dev.sh all

## Start only the database and API on http://127.0.0.1:8000 (docs at /docs)
dev-api:
	@scripts/dev.sh api

## Start only the web app on http://127.0.0.1:5173 (run the API separately)
dev-web:
	@scripts/dev.sh web

## Start Postgres + PostGIS and wait until it accepts connections
db-up:
	docker compose up -d --wait db

## Stop the database and route planner (data is kept in a Docker volume)
db-down:
	docker compose down

## Delete the database volume and start fresh
db-reset:
	docker compose down -v
	docker compose up -d --wait db

## Apply database migrations to the development database
migrate:
	cd backend && uv run alembic upgrade head

## Run the backend tests (needs `make db-up`)
test:
	cd backend && uv run pytest

## Run the frontend unit tests
test-web:
	cd frontend && npm test

## Run the browser end-to-end tests (desktop and phone)
e2e:
	cd frontend && npm run e2e

## Check linting and formatting (backend and frontend)
lint:
	cd backend && uv run ruff check . && uv run ruff format --check .
	cd frontend && npm run lint

## Fix backend lint issues and format code
format:
	cd backend && uv run ruff check --fix . && uv run ruff format .
