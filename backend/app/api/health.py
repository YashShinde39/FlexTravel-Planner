from fastapi import APIRouter, Request, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health(request: Request, response: Response) -> dict[str, str | None]:
    """Liveness plus dependency status: is the database reachable, and is PostGIS installed?"""
    try:
        async with request.app.state.engine.connect() as conn:
            postgis = await conn.scalar(
                text("SELECT extversion FROM pg_extension WHERE extname = 'postgis'")
            )
    except (SQLAlchemyError, OSError):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable", "database": "unreachable", "postgis": None}

    if postgis is None:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable", "database": "ok", "postgis": None}
    return {"status": "ok", "database": "ok", "postgis": postgis}
