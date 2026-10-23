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

## Getting started

Prerequisites: [OrbStack](https://orbstack.dev) (or another Docker), [uv](https://docs.astral.sh/uv/)
and Node.js 20.19+.

```bash
make install   # backend and frontend dependencies
make dev       # database + API + web app in one terminal; Ctrl+C stops them
```

Then open http://127.0.0.1:5173 (app) or http://127.0.0.1:8000/docs (API).

To debug one side, run them in separate terminals: `make dev-api` and `make dev-web`.

| Command | What it does |
| --- | --- |
| `make test` / `make test-web` / `make e2e` | Backend tests / frontend unit tests / browser tests |
| `make lint` | Lint backend and frontend |
| `make db-down` / `make db-reset` | Stop the database / wipe it and start fresh |

### Troubleshooting

| Message | Fix |
| --- | --- |
| `Docker isn't running` | Open OrbStack and run the command again. |
| `Port 8000 is busy` / `Port 5173 is busy` | Another dev server is still running (perhaps in another terminal). Stop it with Ctrl+C, or pick other ports: `API_PORT=8001 WEB_PORT=5174 make dev`. |
| `VIRTUAL_ENV ... does not match the project environment` | A different Python environment is active in your shell. Harmless, but `deactivate` removes it. |
| `No rule to make target` | Run `make` from the repository root (the folder containing `Makefile`). |

More detail: [backend/README.md](backend/README.md), [frontend/README.md](frontend/README.md).

## Data

Transit data: Open Transit Data, Department of Transport, Government of NCT of Delhi
([otd.delhi.gov.in](https://otd.delhi.gov.in)). Feed files are not included in this
repository; see [ADR-0011](docs/decisions/0011-data-sources-and-licensing.md).
