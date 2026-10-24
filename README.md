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
  Until it's built, OpenTripPlanner runs behind the same interface
  ([ADR-0014](docs/decisions/0014-interim-routing-engine.md)).
- Stack: FastAPI, PostgreSQL + PostGIS, React + TypeScript, MapLibre ([ADR-0013](docs/decisions/0013-frontend-architecture.md)).

## Getting started

Prerequisites: [OrbStack](https://orbstack.dev) (or another Docker), [uv](https://docs.astral.sh/uv/)
and Node.js 20.19+.

```bash
make install   # backend and frontend dependencies
make data      # first time only: map, bus, Metro and station data + route planner graph (~2 min)
make dev       # database + route planner + API + web app; Ctrl+C stops them
```

`make data` needs the bus feed in `data/raw/` first: see [data/README.md](data/README.md)
(one `curl` command).

Then open http://127.0.0.1:5173 (app) or http://127.0.0.1:8000/docs (API).

To debug one side, run them in separate terminals: `make dev-api` and `make dev-web`.

### Google Maps (optional)

The app shows Google Maps when given a key (ADR-0017), and a free OpenStreetMap map
otherwise. To use Google Maps, create `frontend/.env.local` (git ignores it) with:

```bash
VITE_GOOGLE_MAPS_API_KEY=your-browser-key
VITE_GOOGLE_MAPS_MAP_ID=your-map-id
```

then restart `make dev`. Getting both, in the [Google Cloud console](https://console.cloud.google.com/google/maps-apis):

1. Create a project and link a billing account (map loads are free up to Google's
   monthly quota). Set a budget alert under Billing.
2. Enable the **Maps JavaScript API**.
3. **Keys & Credentials → Create credentials → API key.** Restrict it: application
   restriction *Websites* (`http://127.0.0.1:5173/*`, `http://localhost:5173/*`, and your
   production address), API restriction *Maps JavaScript API*.
4. **Map Management → Create map ID**, type *JavaScript*, *Vector*. Copy its ID.

| Command | What it does |
| --- | --- |
| `make test` / `make test-web` / `make e2e` | Backend tests / frontend unit tests / browser tests |
| `make lint` | Lint backend and frontend |
| `make data` | Rebuild the planner's data, e.g. after downloading a newer feed |
| `make db-down` / `make db-reset` | Stop the database and planner / wipe the database and start fresh |

### Troubleshooting

| Message | Fix |
| --- | --- |
| `Docker isn't running` | Open OrbStack and run the command again. |
| `Port 8000 is busy` / `Port 5173 is busy` | Another dev server is still running (perhaps in another terminal). Stop it with Ctrl+C, or pick other ports: `API_PORT=8002 WEB_PORT=5175 make dev` (8001/5174 are the prototype's). |
| `Route planning is off until the data is prepared` | Run `make data` once, then `make dev` again. |
| Search shows stops but no landmarks or addresses | Landmark search uses Photon, a public service; it may be briefly unavailable. Stops and stations keep working. |
| `VIRTUAL_ENV ... does not match the project environment` | A different Python environment is active in your shell. Harmless, but `deactivate` removes it. |
| `No rule to make target` | Run `make` from the repository root (the folder containing `Makefile`). |

More detail: [backend/README.md](backend/README.md), [frontend/README.md](frontend/README.md).

## Data

Transit data: Open Transit Data, Department of Transport, Government of NCT of Delhi
([otd.delhi.gov.in](https://otd.delhi.gov.in)). Feed files are not included in this
repository; see [ADR-0011](docs/decisions/0011-data-sources-and-licensing.md).
