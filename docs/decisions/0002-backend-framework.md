# ADR-0002: FastAPI backend, React + TypeScript frontend, monorepo

- Status: Accepted
- Date: 2026-10-23

## Context

An initial scaffold used Django + Django REST Framework, and was never merged. The backend
mostly serves one heavy endpoint (plan a journey) plus lookups (stop and landmark search),
backed by Python data tooling for GTFS processing.

## Decision

- **Backend:** FastAPI, with Pydantic for request/response validation, SQLAlchemy 2.0 and
  Alembic migrations.
- **Frontend:** React + TypeScript, built with Vite and styled with Tailwind CSS.
- **Repo layout:** one monorepo, with `backend/` and `frontend/` side by side.

## Alternatives considered

- **Django + DRF.** Batteries included (admin, ORM, auth), but most of that goes unused
  here, and async support is less central to its design.
- **Flask.** Lighter, but has no built-in validation or OpenAPI generation.
- **Separate repos.** More overhead for a single developer; changes that touch both the API
  and the UI are harder to review together.

## Consequences

- OpenAPI docs come for free at `/docs`, and request validation is declarative.
- **Correction to the original reasoning.** The plan cited "better performance with
  asynchronous routing algorithms". Async improves *I/O concurrency* (database, external
  APIs). It does not make CPU-bound work like RAPTOR faster. Route searches must run in a
  worker thread or process pool so they don't block the event loop. Python's GIL also limits
  how much threads help; a process pool, or a faster language for the core, are possible
  later steps (ADR-0003).
- Frontend types must be kept in sync with Pydantic schemas, by hand at first; they could
  be generated from OpenAPI later.

## Why (in my words)

> _To fill in: what does FastAPI give this project that Django wouldn't? Where does async help and where doesn't it?_

## Questions an interviewer might ask

- Your routing is CPU-bound. Why does async matter at all?
- What happens to other requests while one route search is running?
- How do you keep frontend and backend types in sync?
