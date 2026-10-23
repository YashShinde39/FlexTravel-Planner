from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine

from app.api import health
from app.core.config import Settings, get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    # Connections are opened lazily, so the app starts even if the database is down;
    # /api/health reports that instead. The timeout keeps health checks from hanging.
    app.state.engine = create_async_engine(
        settings.database_url, pool_pre_ping=True, connect_args={"timeout": 5}
    )
    yield
    await app.state.engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(title="FlexTravel Planner API", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings or get_settings()
    app.include_router(health.router)
    return app


app = create_app()
