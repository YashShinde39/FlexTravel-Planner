# ADR-0009: Vercel + managed FastAPI host + managed Postgres

- Status: Accepted
- Date: 2026-10-23

## Context

A public demo URL matters for interviews. The stack is a static React app, a Python API
that holds the transit network in memory, and Postgres + PostGIS.

## Decision

- **Frontend:** Vercel.
- **Backend:** a managed container/app host (Render or Fly.io; chosen when we deploy).
- **Database:** managed Postgres with PostGIS (Neon or Supabase).

Free tiers where possible.

## Alternatives considered

- **Single Docker host (VPS).** Full control and more ops learning, but you maintain the
  server.
- **Local only.** Defers the work but leaves no shareable demo.

## Consequences

- The in-memory network must fit within the backend host's memory limit. Delhi's size is
  measured in M1 and could force a paid tier or a more compact representation.
- Free-tier hosts may sleep when idle, so the first request after a pause is slow while
  the network reloads. A loading state or a warm-up ping mitigates this.
- CORS and environment configuration are needed across three providers.

## Why (in my words)

> _To fill in: why managed services over your own server, for this project?_

## Questions an interviewer might ask

- What happens on a cold start? How long does loading the network take?
- How would you scale to many concurrent route searches?
