import asyncio
from typing import Annotated

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel

from app.places.search import Place, merge, search_local

router = APIRouter(prefix="/api/v1", tags=["places"])


class PlaceSearchResponse(BaseModel):
    places: list[Place]


@router.get("/places")
async def search_places(
    request: Request, q: Annotated[str, Query(min_length=2, max_length=100)]
) -> PlaceSearchResponse:
    """Suggestions for the From/To fields: stations and stops, then landmarks and addresses."""
    photon = request.app.state.photon
    local, remote = await asyncio.gather(
        search_local(request.app.state.engine, q),
        photon.search(q) if photon else asyncio.sleep(0, result=[]),
    )
    return PlaceSearchResponse(places=merge(local, remote))
