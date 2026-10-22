# Roadmap

Milestones are delivered as small PRs (ADR-0010). There is no fixed deadline; each
milestone ships something that works before the next one starts.

## M1: Delhi data

1. **Feed inspection.** Download the DTC bus, Delhi Metro and NCRTC feeds and write a
   report on what's actually in them: sizes, service calendars, fare files, coordinate
   quality, times past midnight, stops that should be shared between agencies. The
   decisions that depend on this are fare handling (ADR-0006), bus buffers (ADR-0007) and
   memory budget (ADR-0009).
2. **Backend skeleton.** FastAPI, Docker Compose with Postgres + PostGIS, Alembic, CI.
3. **Import.** Load stops, routes, trips, stop times and calendars for all three agencies.
4. **Transfers** *(owner-built)*. Link stops across agencies with walking footpaths.
5. **Estimated-time flags** and transfer buffers for buses.

## M2: RAPTOR *(guided build)*

6. RAPTOR explainer with a worked example on a toy network.
7. Data structures for RAPTOR (routes, trips, footpaths) built from the database.
8. Skeleton and failing tests; the owner implements the rounds.
9. Run on all of Delhi: measure, profile, optimise.

## M3: First usable product

10. Frontend skeleton (Vite + TypeScript + Tailwind + Leaflet map).
11. Plan endpoint and stop search API.
12. Results UI with step-by-step directions.
13. Deploy (ADR-0009).

## M4: Trade-offs

14. McRAPTOR with fares (feed data + official tables).
15. Auto-rickshaw and app cab access legs.
16. Reliability score and labels.

## M5: Visitor features

17. OpenStreetMap landmark import and search.
18. Map pin origin/destination; Nominatim address search.
