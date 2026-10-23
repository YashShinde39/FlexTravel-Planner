# ADR-0005: PostgreSQL + PostGIS

- Status: Accepted
- Date: 2026-10-23

## Context

Delhi's feeds contain thousands of stops and a large `stop_times` table. Several features
are spatial queries:

- stops within walking distance of a point (access/egress);
- bus stops near each metro station (transfer linking);
- landmarks near a map pin.

Routing itself runs on in-memory structures built from the database (ADR-0003), not on
database queries.

## Decision

Use **PostgreSQL with the PostGIS extension**: Docker locally, managed in production
(ADR-0009). Schema changes go through **Alembic** migrations.

## Alternatives considered

- **SQLite + in-memory spatial index (KD-tree).** No server to run, but less realistic,
  and spatial logic would be hand-written.
- **PostgreSQL without PostGIS.** Distance maths in Python reinvents spatial indexes.
- **Graph database (Neo4j).** Transit data is tabular (GTFS), and routing happens in
  memory, so a graph database would add operational cost without speeding up search.

## Consequences

- Spatial queries use GiST indexes and `ST_DWithin` on `geography` columns.
- Local development requires Docker.
- The production host must support PostGIS (Neon and Supabase both do).

## Why (in my words)

> _To fill in: what does PostGIS give you that plain Postgres doesn't? Why not a graph database for a "graph" problem?_

## Questions an interviewer might ask

- How does a spatial index find nearby points without checking every row?
- Why `geography` instead of `geometry`?
- If routing is in memory, what is the database for?
