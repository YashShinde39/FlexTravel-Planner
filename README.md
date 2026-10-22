# FlexTravel Planner

A multi-modal public transport journey planner for India, starting with Delhi NCR
(DTC buses, Delhi Metro, NCRTC). It shows visitors several route options that trade off
travel time, number of changes and fare, including auto-rickshaw and cab legs for the
first and last mile.

**Status:** early development. See the [roadmap](docs/roadmap.md).

## Design

- [Architecture decision records](docs/decisions/README.md): what was decided, the
  alternatives, and why.
- Routing: RAPTOR, extended to McRAPTOR ([ADR-0003](docs/decisions/0003-routing-algorithm.md)).
- Stack: FastAPI, PostgreSQL + PostGIS, React + TypeScript.
