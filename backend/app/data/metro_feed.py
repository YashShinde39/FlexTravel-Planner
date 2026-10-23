"""Generate a GTFS feed for the Delhi Metro, Rapid Metro and Namo Bharat (ADR-0016).

    uv run python -m app.data.metro_feed ../data/work/metro/routes.opl \
        ../data/work/otp/metro.gtfs.zip

There is no official timetable to download (ADR-0011), so one is built:

1. Stations and track come from OpenStreetMap: each line's route relation lists its stops
   in order, and the distance between two stops is measured along the line's own track.
2. The time between two stations is a fixed stop overhead plus the distance at a running
   speed. Speeds are calibrated per line so that published end-to-end times come out
   right (metro_lines.SPEED_CHECKS).
3. Trains run at the frequencies in metro_lines.LINES, from the first to the last train,
   written as GTFS frequencies.
4. Stops that share a name (and lie close together) form one station. At interchanges,
   its mapped entrances and a platform per line are joined by walkways (GTFS pathways)
   sized so that changing lines takes the minutes in metro_lines.CHANGE_MIN.

All times are estimates; the API marks them so. When the official feed can be downloaded
it replaces this one with no code change.
"""

import argparse
import csv
import heapq
import io
import math
import re
import zipfile
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from app.data import metro_lines, opl
from app.data.metro_lines import Line

# Calendar: one service for Monday to Saturday and one for Sunday, valid for years ahead
# (the engine loads only a window around today). Public holidays aren't modelled.
SERVICE_START, SERVICE_END = "20260101", "20991231"
DAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
# Stops with the same name further apart than this are different stations.
SAME_STATION_RADIUS_M = 800
# If the track between two stops can't be followed, assume it's this much longer than a
# straight line (the real lines measure 2-10% longer).
DETOUR_FACTOR = 1.15
# Peak hours on weekdays, as [start, end) in hours.
PEAKS = ((8, 11), (17, 21))
LATE_FROM = 21
# Mapped station entrances (railway=subway_entrance) this close belong to the station.
ENTRANCE_RADIUS_M = 350
# Walking pace inside stations, for the extra walk from a far entrance.
WALK_SPEED_MS = 1.3
# OSM colours are mostly hex, a few are names.
NAMED_COLOURS = {"gray": "808080", "grey": "808080"}

# "Hauz Khas (Yellow Line)": OSM names interchange stops once per line.
LINE_SUFFIX = re.compile(r"\s*\([\w ]+ Line\)$")


def station_name(stop_name: str) -> str:
    """The station a stop belongs to: "Hauz Khas (Yellow Line)" -> "Hauz Khas"."""
    name = LINE_SUFFIX.sub("", stop_name)
    return metro_lines.SAME_STATION.get(name, name)


def display_name(stop_name: str) -> str:
    return LINE_SUFFIX.sub("", stop_name)


def distance_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Great-circle distance between two (lon, lat) points."""
    lon1, lat1, lon2, lat2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + (
        math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * 6_371_000 * math.asin(math.sqrt(h))


@dataclass
class Stop:
    node: int
    name: str  # as mapped, e.g. "Hauz Khas (Yellow Line)"
    position: tuple[float, float]  # (lon, lat)


@dataclass
class Pattern:
    """One direction of a line: its stops in order and the track between them."""

    line: Line
    relation: int
    stops: list[Stop]
    segments_m: list[float]  # along-track distance from each stop to the next
    shape: list[tuple[float, float]]  # the track, stop to stop
    straight_segments: int = 0  # segments where the track couldn't be followed

    @property
    def length_m(self) -> float:
        return sum(self.segments_m)


class Track:
    """A line's track as a graph of OSM nodes, for measuring distances along it."""

    def __init__(self, data: opl.OsmData, ways: Iterable[int]) -> None:
        self._coords = data.node_coords
        self._edges: dict[int, list[tuple[int, float]]] = defaultdict(list)
        for way in ways:
            nodes = [n for n in data.way_nodes.get(way, []) if n in self._coords]
            for a, b in zip(nodes, nodes[1:], strict=False):
                d = distance_m(self._coords[a], self._coords[b])
                self._edges[a].append((b, d))
                self._edges[b].append((a, d))

    def nearest(self, position: tuple[float, float]) -> int | None:
        return min(self._edges, key=lambda n: distance_m(self._coords[n], position), default=None)

    def path(self, start: int, end: int) -> tuple[float, list[tuple[float, float]]] | None:
        """Shortest distance along the track, and the points on the way (Dijkstra)."""
        best = {start: 0.0}
        previous: dict[int, int] = {}
        queue = [(0.0, start)]
        while queue:
            cost, node = heapq.heappop(queue)
            if node == end:
                points = [self._coords[end]]
                while node != start:
                    node = previous[node]
                    points.append(self._coords[node])
                return cost, points[::-1]
            if cost > best[node]:
                continue
            for neighbour, length in self._edges[node]:
                if cost + length < best.get(neighbour, math.inf):
                    best[neighbour] = cost + length
                    previous[neighbour] = node
                    heapq.heappush(queue, (cost + length, neighbour))
        return None


def build_pattern(data: opl.OsmData, line: Line, relation: int) -> Pattern:
    members = data.relation_members.get(relation)
    if members is None:
        raise ValueError(f"{line.name}: OSM relation {relation} isn't in the extract")
    stops = [
        Stop(m.ref, data.node_tags.get(m.ref, {}).get("name", ""), data.node_coords[m.ref])
        for m in members
        if m.type == "n" and m.role.startswith("stop") and m.ref in data.node_coords
    ]
    if len(stops) < 2:
        raise ValueError(f"{line.name}: relation {relation} has fewer than two stops")
    if unnamed := [s.node for s in stops if not s.name]:
        raise ValueError(f"{line.name}: stops without a name in relation {relation}: {unnamed}")

    # The route's track is its members with an empty role (platforms have role "platform").
    track = Track(data, (m.ref for m in members if m.type == "w" and m.role == ""))
    pattern = Pattern(line, relation, stops, segments_m=[], shape=[stops[0].position])
    for a, b in zip(stops, stops[1:], strict=False):
        start, end = track.nearest(a.position), track.nearest(b.position)
        found = track.path(start, end) if start is not None and end is not None else None
        if found:
            length, points = found
            pattern.segments_m.append(length)
            pattern.shape.extend(points[1:])
        else:
            pattern.segments_m.append(distance_m(a.position, b.position) * DETOUR_FACTOR)
            pattern.shape.append(b.position)
            pattern.straight_segments += 1
    return pattern


def running_speeds(patterns: dict[str, list[Pattern]]) -> dict[str, float]:
    """Metres per second between stops, per line, from the published end-to-end times.

    A journey of n segments takes n * STOP_OVERHEAD_S plus distance / speed, so the speed
    that reproduces a published time T is distance / (T - n * overhead).
    """
    calibrated = {}
    for line_id, (minutes, _source) in metro_lines.SPEED_CHECKS.items():
        pattern = patterns[line_id][0]
        moving_s = minutes * 60 - len(pattern.segments_m) * metro_lines.STOP_OVERHEAD_S
        calibrated[line_id] = pattern.length_m / moving_s
    return {line.id: calibrated[line.speed_from] for line in metro_lines.LINES}


def segment_seconds(distance: float, speed: float) -> int:
    return round(metro_lines.STOP_OVERHEAD_S + distance / speed)


def journey_seconds(pattern: Pattern, speed: float) -> int:
    return sum(segment_seconds(d, speed) for d in pattern.segments_m)


def _seconds(clock: str) -> int:
    hours, minutes = map(int, clock.split(":"))
    return hours * 3600 + minutes * 60


def _clock(seconds: int) -> str:
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


def frequency_bands(line: Line, service: str) -> list[tuple[int, int, int]]:
    """(start, end, headway) in seconds: trains leave every `headway` from `start` until
    before `end`. The last band ends just after the last train."""
    headways, hours = line.headways, line.hours
    last = _seconds(hours.last) + 60
    if service == "sunday":
        return [(_seconds(hours.sunday_first), last, round(headways.sunday * 60))]

    edges = {_seconds(hours.first), last, LATE_FROM * 3600}
    edges |= {hour * 3600 for peak in PEAKS for hour in peak}
    edges = sorted(e for e in edges if _seconds(hours.first) <= e <= last)
    bands = []
    for start, end in zip(edges, edges[1:], strict=False):
        hour = start // 3600
        if any(a <= hour < b for a, b in PEAKS):
            minutes = headways.peak
        elif hour >= LATE_FROM:
            minutes = headways.late
        else:
            minutes = headways.day
        bands.append((start, end, round(minutes * 60)))
    return bands


@dataclass
class Station:
    id: str
    name: str
    stops: list[Stop] = field(default_factory=list)
    lines: set[str] = field(default_factory=set)

    @property
    def position(self) -> tuple[float, float]:
        lons, lats = zip(*(s.position for s in self.stops), strict=True)
        return sum(lons) / len(lons), sum(lats) / len(lats)


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def group_stations(patterns: Iterable[Pattern]) -> dict[int, Station]:
    """Station of each stop node: stops with the same station name, close together."""
    by_name: dict[str, list[Station]] = defaultdict(list)
    station_of: dict[int, Station] = {}
    for pattern in patterns:
        for stop in pattern.stops:
            if stop.node in station_of:
                station_of[stop.node].lines.add(pattern.line.id)
                continue
            name = station_name(stop.name)
            station = next(
                (
                    s
                    for s in by_name[name]
                    if distance_m(s.position, stop.position) <= SAME_STATION_RADIUS_M
                ),
                None,
            )
            if station is None:
                suffix = f"-{len(by_name[name]) + 1}" if by_name[name] else ""
                station = Station(id=f"{_slug(name)}{suffix}", name=name)
                by_name[name].append(station)
            station.stops.append(stop)
            station.lines.add(pattern.line.id)
            station_of[stop.node] = station
    return station_of


def colour(tags: dict[str, str]) -> str:
    value = tags.get("colour", "").strip().lstrip("#").lower()
    value = NAMED_COLOURS.get(value, value)
    return value.upper() if re.fullmatch(r"[0-9a-f]{6}", value) else "666666"


def text_colour(background: str) -> str:
    """Black or white, whichever reads better on the line's colour (WCAG luminance)."""

    def channel(hex_pair: str) -> float:
        c = int(hex_pair, 16) / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(background[i : i + 2]) for i in (0, 2, 4))
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "000000" if luminance > 0.4 else "FFFFFF"


@dataclass
class Report:
    lines: list[str] = field(default_factory=list)
    stations: int = 0
    interchanges: int = 0
    modelled_interchanges: int = 0  # with entrances mapped, so change times apply
    warnings: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        parts = [
            *self.lines,
            f"{self.stations} stations, {self.interchanges} where lines meet, "
            f"{self.modelled_interchanges} of them with change times",
        ]
        return "\n".join(parts + [f"warning: {w}" for w in self.warnings])


def _write(out: zipfile.ZipFile, name: str, rows: list[dict]) -> None:
    with out.open(name, "w") as raw, io.TextIOWrapper(raw, encoding="utf-8", newline="") as text:
        writer = csv.DictWriter(text, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def generate(
    data: opl.OsmData, target: Path, entrances: Iterable[tuple[float, float]] = ()
) -> Report:
    report = Report()
    patterns = {
        line.id: [build_pattern(data, line, relation) for relation in line.relations]
        for line in metro_lines.LINES
    }
    speeds = running_speeds(patterns)
    all_patterns = [p for line_patterns in patterns.values() for p in line_patterns]
    station_of = group_stations(all_patterns)
    stations = {s.id: s for s in station_of.values()}

    for line in metro_lines.LINES:
        first = patterns[line.id][0]
        minutes = journey_seconds(first, speeds[line.id]) / 60
        published = metro_lines.SPEED_CHECKS.get(line.id) or metro_lines.TIME_REPORTS.get(line.id)
        check = f", published {published[0]} min ({published[1]})" if published else ""
        report.lines.append(
            f"{line.id}: {first.length_m / 1000:.1f} km, {len(first.stops)} stops, "
            f"{speeds[line.id] * 3.6:.0f} km/h between stops, {minutes:.0f} min end to end"
            f"{check}"
        )
        for pattern in patterns[line.id]:
            if pattern.straight_segments:
                report.warnings.append(
                    f"{line.id} (relation {pattern.relation}): {pattern.straight_segments} "
                    "gaps in the track, measured as straight lines"
                )

    # Interchanges are modelled inside: entrances on the street and one platform per line,
    # joined by walkways (GTFS pathways). A walkway takes half the station's change time
    # plus the walk from its entrance, so changing lines (platform -> entrance -> platform)
    # takes at least the change time, and entering from the street about half of it. The
    # engine can then no longer shortcut along the streets outside, which miss skywalks and
    # deep platforms.
    #
    # Only entrances mapped in OpenStreetMap are used: they sit on footways the engine can
    # reach. Entrances guessed at the station's middle or at the platforms often landed on
    # walkways inside the station that don't reach the street, cutting the station off.
    # Other stations are plain platforms, which the engine links to the street itself.
    platform_positions: dict[tuple[str, str], list[tuple[float, float]]] = defaultdict(list)
    for pattern in all_patterns:
        for stop in pattern.stops:
            positions = platform_positions[(station_of[stop.node].id, pattern.line.id)]
            if stop.position not in positions:
                positions.append(stop.position)
    mapped_entrances: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for position in entrances:
        nearest = min(stations.values(), key=lambda s: distance_m(s.position, position))
        if distance_m(nearest.position, position) <= ENTRANCE_RADIUS_M:
            mapped_entrances[nearest.id].append(position)

    def row(
        stop_id: str, name: str, position: tuple[float, float], location_type: int, parent: str = ""
    ) -> dict:
        lon, lat = position
        return {
            "stop_id": stop_id,
            "stop_name": name,
            "stop_lat": f"{lat:.6f}",
            "stop_lon": f"{lon:.6f}",
            "location_type": location_type,
            "parent_station": parent,
        }

    stop_rows, pathway_rows = [], []
    for station in sorted(stations.values(), key=lambda s: s.id):
        stop_rows.append(row(station.id, station.name, station.position, 1))
        platforms = {}
        for line_id in sorted(station.lines):
            positions = platform_positions[(station.id, line_id)]
            platforms[f"{station.id}:{line_id}"] = (
                sum(p[0] for p in positions) / len(positions),
                sum(p[1] for p in positions) / len(positions),
            )
            stop_rows.append(
                row(
                    f"{station.id}:{line_id}",
                    station.name,
                    platforms[f"{station.id}:{line_id}"],
                    0,
                    station.id,
                )
            )
        if len(station.lines) < 2:
            continue
        if not mapped_entrances[station.id]:
            report.warnings.append(
                f"{station.name}: no entrances mapped in OpenStreetMap, so changing lines "
                "there takes the engine's walk along the streets, not the change time"
            )
            continue
        report.modelled_interchanges += 1
        half_change = metro_lines.CHANGE_MIN.get(station.name, metro_lines.DEFAULT_CHANGE_MIN) * 30
        for index, position in enumerate(mapped_entrances[station.id]):
            entrance = f"{station.id}:entrance-{index + 1}"
            stop_rows.append(row(entrance, station.name, position, 2, station.id))
            for platform, platform_position in platforms.items():
                pathway_rows.append(
                    {
                        "pathway_id": f"{entrance}:{platform.split(':')[1]}",
                        "from_stop_id": entrance,
                        "to_stop_id": platform,
                        "pathway_mode": 1,  # walkway
                        "is_bidirectional": 1,
                        "traversal_time": half_change
                        + round(distance_m(position, platform_position) / WALK_SPEED_MS),
                    }
                )

    route_rows, trip_rows, stop_time_rows, frequency_rows, shape_rows = [], [], [], [], []
    for line in metro_lines.LINES:
        first = patterns[line.id][0]
        background = colour(data.relation_tags[first.relation])
        route_rows.append(
            {
                "route_id": line.id,
                "agency_id": line.agency,
                "route_short_name": line.name,
                "route_long_name": (
                    f"{display_name(first.stops[0].name)} – {display_name(first.stops[-1].name)}"
                ),
                "route_type": line.route_type,
                "route_color": background,
                "route_text_color": text_colour(background),
            }
        )
        for direction, pattern in enumerate(patterns[line.id]):
            shape_id = f"{line.id}-{pattern.relation}"
            shape_rows += [
                {
                    "shape_id": shape_id,
                    "shape_pt_lat": f"{lat:.6f}",
                    "shape_pt_lon": f"{lon:.6f}",
                    "shape_pt_sequence": index,
                }
                for index, (lon, lat) in enumerate(pattern.shape)
            ]
            for service in ("weekday", "sunday"):
                trip_id = f"{line.id}-{pattern.relation}-{service}"
                trip_rows.append(
                    {
                        "route_id": line.id,
                        "service_id": service,
                        "trip_id": trip_id,
                        "trip_headsign": display_name(pattern.stops[-1].name),
                        "direction_id": direction % 2,
                        "shape_id": shape_id,
                    }
                )
                # Times are relative to the first stop; the frequencies set when trains leave.
                elapsed = 0
                for sequence, stop in enumerate(pattern.stops):
                    if sequence:
                        elapsed += segment_seconds(
                            pattern.segments_m[sequence - 1], speeds[line.id]
                        )
                    stop_time_rows.append(
                        {
                            "trip_id": trip_id,
                            "arrival_time": _clock(elapsed),
                            "departure_time": _clock(elapsed),
                            "stop_id": f"{station_of[stop.node].id}:{line.id}",
                            "stop_sequence": sequence,
                        }
                    )
                frequency_rows += [
                    {
                        "trip_id": trip_id,
                        "start_time": _clock(start),
                        "end_time": _clock(end),
                        "headway_secs": headway,
                        # 1: trains leave exactly every headway from the band's start, so
                        # the engine sees real departures (with 0 it lets you board at any
                        # moment, which breaks connections between lines).
                        "exact_times": 1,
                    }
                    for start, end, headway in frequency_bands(line, service)
                ]

    report.interchanges = sum(len(s.lines) > 1 for s in stations.values())
    report.stations = len(stations)
    unused = set(metro_lines.CHANGE_MIN) - {s.name for s in stations.values() if len(s.lines) > 1}
    report.warnings += [f"change time for {name}, which isn't an interchange" for name in unused]

    used_agencies = {line.agency for line in metro_lines.LINES}
    files = {
        "agency.txt": [
            {
                "agency_id": a.id,
                "agency_name": a.name,
                "agency_url": a.url,
                "agency_timezone": "Asia/Kolkata",
                "agency_lang": "en",
            }
            for a in metro_lines.AGENCIES.values()
            if a.id in used_agencies
        ],
        "stops.txt": stop_rows,
        "routes.txt": route_rows,
        "trips.txt": trip_rows,
        "stop_times.txt": stop_time_rows,
        "frequencies.txt": frequency_rows,
        "shapes.txt": shape_rows,
        "pathways.txt": pathway_rows,
        "calendar.txt": [
            {
                "service_id": service,
                **{day: int(runs) for day, runs in zip(DAYS, days, strict=True)},
                "start_date": SERVICE_START,
                "end_date": SERVICE_END,
            }
            for service, days in (("weekday", [1] * 6 + [0]), ("sunday", [0] * 6 + [1]))
        ],
        "feed_info.txt": [
            {
                "feed_publisher_name": "FlexTravel, generated from OpenStreetMap and "
                "published Delhi Metro and NCRTC information",
                "feed_publisher_url": "https://github.com/YashShinde39/FlexTravel-Planner",
                "feed_lang": "en",
                "feed_version": f"{date.today():%Y%m%d} (data as of {metro_lines.AS_OF})",
            }
        ],
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(".partial")
    with zipfile.ZipFile(partial, "w", zipfile.ZIP_DEFLATED) as out:
        for name, rows in files.items():
            if rows:
                _write(out, name, rows)
    partial.replace(target)  # only a complete file ever appears under the final name
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("routes", type=Path, help="Metro route relations as OPL (data/work/)")
    parser.add_argument("target", type=Path, help="GTFS zip to write (data/work/otp/)")
    parser.add_argument(
        "--entrances", type=Path, help="Metro station entrances as OPL (data/work/)"
    )
    args = parser.parse_args()
    entrances = opl.read(args.entrances).node_coords.values() if args.entrances else ()
    print(generate(opl.read(args.routes), args.target, entrances))
    print(f"wrote {args.target}")


if __name__ == "__main__":
    main()
