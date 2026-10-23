# Backend

FastAPI + SQLAlchemy (async, asyncpg) + Alembic, on PostgreSQL 17 with PostGIS 3.5
(ADR-0002, ADR-0005).

## Setup

Requires [uv](https://docs.astral.sh/uv/) and Docker ([OrbStack](https://orbstack.dev) on
macOS). From the repository root:

```bash
make db-up     # Postgres + PostGIS on localhost:5433 (creates flextravel and flextravel_test)
make migrate   # apply migrations to the development database
make dev-api   # API on http://127.0.0.1:8000, interactive docs at /docs (`make dev` also starts the web app)
make test      # tests run against flextravel_test
```

`uv` installs Python 3.14 and the locked dependencies into `backend/.venv` on first use.

## Layout

```
app/
  main.py         app factory; lifespan creates the database engine
  core/config.py  settings from FLEXTRAVEL_* environment variables
  api/health.py   GET /api/health: database and PostGIS status
migrations/       Alembic (async); 0001 enables PostGIS
tests/            pytest; the test database is migrated once per run
docker/           init script that creates the test database
```

## Configuration

| Variable | Default |
| --- | --- |
| `FLEXTRAVEL_ENVIRONMENT` | `development` |
| `FLEXTRAVEL_DATABASE_URL` | `postgresql+asyncpg://flextravel:flextravel@localhost:5433/flextravel` |
| `FLEXTRAVEL_TEST_DATABASE_URL` (tests only) | same server, database `flextravel_test` |

## Migrations

```bash
cd backend
uv run alembic revision -m "describe the change"   # then edit the generated file
uv run alembic upgrade head
```

## Notes

- The official PostGIS image is amd64-only. On Apple Silicon, Docker runs it under
  emulation (`platform: linux/amd64` in `docker-compose.yml`), so local and CI use the
  identical image.
- The database healthcheck uses TCP on purpose. On first start, Postgres runs a temporary
  socket-only server while it creates databases, and a socket check would report "ready"
  too early.
