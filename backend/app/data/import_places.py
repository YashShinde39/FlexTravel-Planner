"""Load searchable places into Postgres: bus stops from the feed, stations from OSM.

    uv run python -m app.data.import_places ../data/work/otp/dtc-bus.gtfs.zip \
        ../data/work/stations.geojsonseq

Replaces the whole `places` table in one transaction, so re-running is safe.

- **Bus stops:** a stop usually exists once on each side of the road under the same name.
  Suggestions should show "Laxminarain Temple" once, so same-name stops within
  `SAME_NAME_RADIUS_M` are merged into one place at their midpoint. Routing is unaffected:
  the engine walks to whichever side the bus actually stops on.
- **Stations:** OpenStreetMap `railway=station` features (ODbL). Interchanges are mapped
  once per line, so same-name stations within the radius are merged too.
"""

import argparse
import asyncio
import csv
import io
import json
import math
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings

SAME_NAME_RADIUS_M = 400
METRO_NETWORKS = {"Delhi Metro", "Rapid Metro Gurgaon", "Pink Line"}
# OSM maps interchange stations once per line: "Hauz Khas (Yellow Line)".
LINE_SUFFIX = re.compile(r"\s*\((\w+) Line\)$")


@dataclass
class Place:
    id: str
    name: str
    kind: str
    detail: str | None
    lat: float
    lon: float
    lines: list[str] = field(default_factory=list)  # metro lines, for interchanges

    @property
    def full_detail(self) -> str | None:
        """'Metro station · Yellow & Magenta lines'."""
        if not self.lines:
            return self.detail
        noun = "line" if len(self.lines) == 1 else "lines"
        return f"{self.detail} · {' & '.join(self.lines)} {noun}"


def normalise(name: str) -> str:
    """What search compares against: lower case, punctuation and extra spaces removed."""
    return " ".join(re.sub(r"[^a-z0-9]+", " ", name.lower()).split())


def distance_m(a, b) -> float:
    """Equirectangular approximation; accurate to well under 1% at city scale."""
    x = math.radians(b.lon - a.lon) * math.cos(math.radians((a.lat + b.lat) / 2))
    y = math.radians(b.lat - a.lat)
    return 6_371_000 * math.hypot(x, y)


def merge_same_name(places: list[Place]) -> list[Place]:
    """Merge places that share a (normalised) name and lie within SAME_NAME_RADIUS_M.

    Each merged place keeps the first member's id, sits at the members' midpoint and lists
    all their metro lines. Places with the same name further apart (e.g. two different
    "Bus Depot" stops) stay separate.
    """
    clusters: dict[str, list[list[Place]]] = {}
    for place in places:
        groups = clusters.setdefault((place.kind, normalise(place.name)), [])
        group = next((g for g in groups if distance_m(g[0], place) <= SAME_NAME_RADIUS_M), None)
        if group is None:
            groups.append([place])
        else:
            group.append(place)

    merged = []
    for groups in clusters.values():
        for group in groups:
            first = group[0]
            merged.append(
                Place(
                    id=first.id,
                    name=first.name,
                    kind=first.kind,
                    detail=first.detail,
                    lat=sum(p.lat for p in group) / len(group),
                    lon=sum(p.lon for p in group) / len(group),
                    lines=sorted({line for p in group for line in p.lines}),
                )
            )
    return merged


def bus_stops(feed_path: Path) -> list[Place]:
    with zipfile.ZipFile(feed_path) as feed, feed.open("stops.txt") as raw:
        rows = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig"))
        return [
            Place(
                id=f"bus:dtc:{row['stop_id']}",
                name=row["stop_name"].strip(),
                kind="bus_stop",
                detail="Bus stop",
                lat=float(row["stop_lat"]),
                lon=float(row["stop_lon"]),
            )
            for row in rows
            if row["stop_name"].strip()
        ]


def stations(geojsonseq_path: Path) -> list[Place]:
    places = []
    with geojsonseq_path.open(encoding="utf-8") as lines:
        for line in lines:
            if not line.strip():
                continue
            feature = json.loads(line.lstrip("\x1e"))  # RFC 8142 record separator
            tags = feature["properties"]
            name = tags.get("name:en") or tags.get("name")
            is_point = feature["geometry"]["type"] == "Point"
            if tags.get("railway") != "station" or not name or not is_point:
                continue
            network = tags.get("network")
            is_metro = tags.get("station") == "subway" or network in METRO_NETWORKS
            line = LINE_SUFFIX.search(name)
            # "Delhi Metro" goes without saying; other networks are worth naming, by the
            # name travellers know (RapidX's trains are "Namo Bharat").
            label = "Metro station" if is_metro else "Railway station"
            if network == "RapidX":
                label = "Namo Bharat station"
            shown_network = network if network == "Rapid Metro Gurgaon" else None
            lon, lat = feature["geometry"]["coordinates"]
            places.append(
                Place(
                    id=f"osm:{feature['id']}",
                    name=LINE_SUFFIX.sub("", name),
                    kind="metro_station" if is_metro else "rail_station",
                    detail=f"{label} · {shown_network}" if shown_network else label,
                    lat=lat,
                    lon=lon,
                    lines=[line.group(1)] if line else [],
                )
            )
    return places


async def replace_places(database_url: str, places: list[Place]) -> None:
    engine = create_async_engine(database_url)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("DELETE FROM places"))
            if not places:
                return
            await conn.execute(
                text(
                    "INSERT INTO places (id, name, kind, detail, search_name, location) "
                    "VALUES (:id, :name, :kind, :detail, :search_name, "
                    "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography)"
                ),
                [
                    {
                        "id": place.id,
                        "name": place.name,
                        "kind": place.kind,
                        "detail": place.full_detail,
                        "search_name": normalise(place.name),
                        "lat": place.lat,
                        "lon": place.lon,
                    }
                    for place in places
                ],
            )
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("bus_feed", type=Path, help="cleaned bus feed zip")
    parser.add_argument("stations", type=Path, help="OSM stations as GeoJSON sequence")
    args = parser.parse_args()

    stops, osm_stations = bus_stops(args.bus_feed), stations(args.stations)
    merged_stops, merged_stations = merge_same_name(stops), merge_same_name(osm_stations)
    asyncio.run(replace_places(get_settings().database_url, merged_stops + merged_stations))
    print(f"bus stops: {len(stops):,} -> {len(merged_stops):,} places (same name, nearby)")
    print(f"stations:  {len(osm_stations):,} -> {len(merged_stations):,} places")


if __name__ == "__main__":
    main()
