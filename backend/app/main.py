from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx2
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine

from app.api import health, places, trips
from app.core.config import Settings, get_settings
from app.places.search import PhotonClient
from app.trips.engine import TripPlanner
from app.trips.otp import OtpPlanner

# Public OSM services ask clients to identify themselves.
USER_AGENT = "FlexTravel-Planner/0.1 (+https://github.com/YashShinde39/FlexTravel-Planner)"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    # Connections are opened lazily, so the app starts even if the database is down;
    # /api/health reports that instead. The timeout keeps health checks from hanging.
    app.state.engine = create_async_engine(
        settings.database_url, pool_pre_ping=True, connect_args={"timeout": 5}
    )
    http = httpx2.AsyncClient(headers={"User-Agent": USER_AGENT})
    app.state.planner = app.state.planner_override or OtpPlanner(http, settings.otp_url)
    app.state.photon = PhotonClient(http, settings.photon_url) if settings.photon_url else None
    yield
    await http.aclose()
    await app.state.engine.dispose()


def create_app(settings: Settings | None = None, planner: TripPlanner | None = None) -> FastAPI:
    """`planner` replaces the routing engine, e.g. with a fake in tests."""
    app = FastAPI(title="FlexTravel Planner API", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings or get_settings()
    app.state.planner_override = planner
    app.include_router(health.router)
    app.include_router(places.router)
    app.include_router(trips.router)
    return app


app = create_app()
