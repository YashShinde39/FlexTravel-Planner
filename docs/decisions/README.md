# Architecture Decision Records

Each file records one significant decision: the context, the options considered, what was
chosen, and its consequences. Decisions are never edited after the fact. To change one,
add a new record that supersedes it.

Every record has a **Why (in my words)** section. Fill it in yourself, without
copying the "Context" text. If you can't write it convincingly, that decision is worth
revisiting before an interview.

| ADR | Decision | Status |
| --- | --- | --- |
| [0001](0001-product-scope.md) | Transit routing for visitors in Delhi NCR (buses + metro), English UI | Accepted |
| [0002](0002-backend-framework.md) | FastAPI backend, React + TypeScript frontend, monorepo | Accepted |
| [0003](0003-routing-algorithm.md) | RAPTOR, extended to McRAPTOR on time, changes and fare | Accepted |
| [0004](0004-access-modes.md) | Walk, auto-rickshaw and app cabs for first and last mile | Accepted |
| [0005](0005-database.md) | PostgreSQL + PostGIS | Accepted |
| [0006](0006-fares.md) | Fares from feed data, with official fare tables as fallback | Accepted |
| [0007](0007-unreliable-bus-times.md) | Transfer buffers and "approximate" labels for bus times | Accepted |
| [0008](0008-locations-and-landmarks.md) | Stop/landmark search, map pins, Nominatim; landmarks from OSM | Accepted |
| [0009](0009-hosting.md) | Vercel + managed FastAPI host + managed Postgres | Accepted |
| [0010](0010-development-workflow.md) | Ownership split, small PRs, restart from scratch | Accepted |
| [0011](0011-data-sources-and-licensing.md) | Official OTD feeds, raw data kept out of git, NCRTC deferred | Accepted |
| [0012](0012-bus-feed-cleaning-and-display.md) | Bus feed cleaning (calendar, duplicate stops) and route-code display | Accepted (1 item pending) |

## Template

```markdown
# ADR-NNNN: Title

- Status: Proposed | Accepted | Superseded by ADR-XXXX
- Date: YYYY-MM-DD

## Context
## Decision
## Alternatives considered
## Consequences
## Why (in my words)
## Questions an interviewer might ask
```
