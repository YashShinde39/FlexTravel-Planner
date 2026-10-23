"""From/To suggestions: our stops and stations first, then landmarks and addresses.

Stops and stations come from Postgres (loaded by `make data`), with trigram matching so
typos and spelling variants still match ("kashmiri gt" -> Kashmere Gate). Landmarks and
addresses come from Photon, an OpenStreetMap geocoder built for search-as-you-type;
Nominatim's usage policy forbids autocomplete (ADR-0008 amended by ADR-0014).
"""

import time
from collections import OrderedDict
from typing import Any, Literal

import httpx2
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.data.import_places import distance_m, normalise

PlaceKind = Literal["metro_station", "rail_station", "bus_stop", "landmark", "address"]

MAX_RESULTS = 8
MAX_LOCAL = 6
# Fuzzy matches at least this similar count as typos of the right name ("rajiv chok" ->
# Rajiv Chowk, 0.82); weaker ones are mostly noise ("india gate" -> IIT Gate, 0.45;
# "hauz khas" -> Hauz Rani, 0.5).
STRONG_SIMILARITY = 0.6
# Delhi NCR (west, south, east, north), the same box as the map and the OSM extract.
NCR_BBOX = "76.6,28.15,77.75,29.0"
DELHI_CENTRE = {"lat": 28.6139, "lon": 77.209}


class Place(BaseModel):
    id: str
    name: str
    detail: str | None
    kind: PlaceKind
    lat: float
    lon: float


class LocalMatch(Place):
    # Matched what was typed (directly or close to it), not just loosely similar.
    direct: bool


# Prefix matches first, then whole-word matches, then fuzzy; stations before stops on ties,
# because a visitor typing "Rajiv Chowk" almost always means the metro station.
_LOCAL_SQL = text(
    """
    SELECT id, name, detail, kind,
           ST_Y(location::geometry) AS lat, ST_X(location::geometry) AS lon,
           (search_name LIKE '%' || :q || '%'
            OR word_similarity(:q, search_name) >= :strong) AS direct
    FROM places
    WHERE search_name LIKE '%' || :q || '%' OR :q <% search_name
    ORDER BY search_name LIKE :q || '%' DESC,
             search_name LIKE '% ' || :q || '%' DESC,
             word_similarity(:q, search_name) DESC,
             CASE kind WHEN 'metro_station' THEN 0 WHEN 'rail_station' THEN 1 ELSE 2 END,
             length(name)
    LIMIT :limit
    """
)


async def search_local(engine: AsyncEngine, query: str, limit: int = MAX_LOCAL) -> list[LocalMatch]:
    q = normalise(query)
    if not q:
        return []
    async with engine.begin() as conn:
        # Default 0.6 is too strict for half-typed words; 0.4 still rejects noise.
        await conn.execute(text("SET LOCAL pg_trgm.word_similarity_threshold = 0.4"))
        params = {"q": q, "limit": limit, "strong": STRONG_SIMILARITY}
        rows = (await conn.execute(_LOCAL_SQL, params)).mappings()
        return [LocalMatch(**row) for row in rows]


class PhotonClient:
    """Photon search with a small in-memory cache, to go easy on the public instance."""

    CACHE_SIZE = 512
    CACHE_TTL_S = 600

    def __init__(self, client: httpx2.AsyncClient, base_url: str) -> None:
        self._client = client
        self._url = f"{base_url.rstrip('/')}/api"
        self._cache: OrderedDict[str, tuple[float, list[Place]]] = OrderedDict()

    async def search(self, query: str) -> list[Place]:
        key = normalise(query)
        if (hit := self._cache.get(key)) and time.monotonic() - hit[0] < self.CACHE_TTL_S:
            self._cache.move_to_end(key)
            return hit[1]
        try:
            response = await self._client.get(
                self._url,
                params={"q": query, "limit": 10, "lang": "en", "bbox": NCR_BBOX, **DELHI_CENTRE},
                timeout=3,
            )
            response.raise_for_status()
            places = [p for f in response.json()["features"] if (p := photon_place(f))]
        except (httpx2.HTTPError, ValueError, KeyError):
            return []  # suggestions degrade to stops and stations only
        self._cache[key] = (time.monotonic(), places)
        if len(self._cache) > self.CACHE_SIZE:
            self._cache.popitem(last=False)
        return places


def photon_place(feature: dict[str, Any]) -> Place | None:
    """Map one Photon result. Skips transit stops and stations: we have better data for those."""
    props = feature["properties"]
    if props.get("osm_key") in {"public_transport", "railway"} or (
        props.get("osm_key") == "highway" and props.get("osm_value") == "bus_stop"
    ):
        return None
    street = " ".join(filter(None, [props.get("housenumber"), props.get("street")]))
    name = props.get("name") or street
    if not name:
        return None
    area = [props.get(k) for k in ("locality", "district", "city", "state")]
    parts = [street if props.get("name") else None, *area]
    detail = ", ".join(dict.fromkeys(part for part in parts if part))
    lon, lat = feature["geometry"]["coordinates"]
    return Place(
        id=f"osm:{props.get('osm_type', '')}{props.get('osm_id', '')}",
        name=name,
        detail=detail or None,
        kind="landmark" if props.get("name") else "address",
        lat=lat,
        lon=lon,
    )


# A landmark this close to one of our stations or stops, and named after it ("Laxmi Nagar
# Metro Station" next to the Laxmi Nagar station), is the same place.
SAME_PLACE_M = 300


def _same_place(remote: Place, local: Place) -> bool:
    return normalise(local.name) in normalise(remote.name) and distance_m(remote, local) < (
        SAME_PLACE_M
    )


def merge(local: list[LocalMatch], remote: list[Place], limit: int = MAX_RESULTS) -> list[Place]:
    """Direct local matches, then landmarks and addresses, then fuzzy-only local matches.

    Fuzzy-only matches ("IIT Gate" for "india gate") are kept for typos, but must not push
    out a landmark that matches what was typed.
    """
    direct = [p for p in local if p.direct]
    fuzzy = [p for p in local if not p.direct]
    remote = [r for r in remote if not any(_same_place(r, p) for p in local)]
    merged: list[Place] = []
    seen: set[tuple[str, str]] = set()
    # Same-name stops far apart are separate places, but listing "AIIMS" twice only
    # confuses; the best-ranked one stands for both, and the planner considers every stop
    # within walking distance of it anyway.
    for place in [*direct, *remote, *fuzzy]:
        key = (place.kind, normalise(place.name))
        if key not in seen:
            seen.add(key)
            merged.append(Place(**place.model_dump(exclude={"direct"})))
    return merged[:limit]
