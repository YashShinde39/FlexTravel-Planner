# FlexTravel Planner

A multi-modal public transport journey planner for India, starting with Delhi NCR
(DTC buses and Delhi Metro). It shows visitors several route options that trade off
travel time, number of changes and fare, including auto-rickshaw and cab legs for the
first and last mile.

**Status:** early development. See the [roadmap](docs/roadmap.md).

## Design

- [Architecture decision records](docs/decisions/README.md): what was decided, the
  alternatives, and why.
- Routing: RAPTOR, extended to McRAPTOR ([ADR-0003](docs/decisions/0003-routing-algorithm.md)).
- Stack: FastAPI, PostgreSQL + PostGIS, React + TypeScript, MapLibre ([ADR-0013](docs/decisions/0013-frontend-architecture.md)).

## Frontend

```bash
cd frontend && npm install && npm run dev   # http://localhost:5173
```

Details in [frontend/README.md](frontend/README.md).

## Data

Transit data: Open Transit Data, Department of Transport, Government of NCT of Delhi
([otd.delhi.gov.in](https://otd.delhi.gov.in)). Feed files are not included in this
repository; see [ADR-0011](docs/decisions/0011-data-sources-and-licensing.md).
