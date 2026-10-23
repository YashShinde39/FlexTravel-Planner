# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas>=2.2,<3", "numpy>=2,<3"]
# ///
"""Inspect GTFS feeds and write a Markdown report of what is actually in them.

Usage (uv installs the dependencies automatically):

    uv run scripts/inspect_gtfs.py \
        --feed bus=data/raw/dtc-bus.zip --feed metro=data/raw/dmrc-metro.zip \
        --out docs/data/feed-inspection.md

The report contains statistics and small samples only, never the feed files themselves
(ADR-0011). Each section notes which design decision it informs.
"""

from __future__ import annotations

import argparse
import hashlib
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

# Rough bounding box of Delhi NCR, used to flag stops with implausible coordinates.
NCR_LAT = (28.0, 29.2)
NCR_LON = (76.7, 77.9)
ROUTE_TYPES = {"0": "tram", "1": "metro/subway", "2": "rail", "3": "bus", "4": "ferry"}
FARE_FILES = ["fare_attributes.txt", "fare_rules.txt", "fare_products.txt",
              "fare_leg_rules.txt", "fare_media.txt", "areas.txt", "stop_areas.txt"]
OPTIONAL_FILES = ["calendar_dates.txt", "frequencies.txt", "transfers.txt", "shapes.txt",
                  "feed_info.txt", "pathways.txt"]
TRANSFER_RADII_M = (200, 400, 800)


@dataclass
class Feed:
    name: str
    path: Path
    tables: dict[str, pd.DataFrame]

    def get(self, file: str) -> pd.DataFrame | None:
        return self.tables.get(file)


def load_feed(name: str, path: Path) -> Feed:
    """Read every .txt in the zip as strings, so nothing is silently converted."""
    tables = {}
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            file = Path(info.filename).name
            if not file.endswith(".txt"):
                continue
            with archive.open(info) as handle:
                frame = pd.read_csv(handle, dtype=str, keep_default_na=False,
                                    encoding="utf-8-sig", skipinitialspace=True)
            frame.columns = [c.strip() for c in frame.columns]
            tables[file] = frame
    return Feed(name, path, tables)


# --------------------------------------------------------------------------- helpers

def gtfs_seconds(times: pd.Series) -> pd.Series:
    """'HH:MM:SS' -> seconds after service-day midnight. Hours may exceed 23. Blank -> NaN."""
    parts = times.str.strip().str.split(":", expand=True)
    if parts.shape[1] != 3:
        return pd.Series(np.nan, index=times.index)
    numbers = parts.apply(pd.to_numeric, errors="coerce")
    return numbers[0] * 3600 + numbers[1] * 60 + numbers[2]


def haversine_m(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = (np.sin((lat2 - lat1) / 2) ** 2
         + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2)
    return 2 * 6_371_000 * np.arcsin(np.sqrt(a))


def clock(seconds: float) -> str:
    if pd.isna(seconds):
        return "n/a"
    seconds = int(seconds)
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}"


def table(headers: list[str], rows: list[list[object]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def pct(part: float, whole: float) -> str:
    return f"{part:,} ({part / whole:.1%})" if whole else str(part)


# --------------------------------------------------------------------------- checks

def inventory(feed: Feed) -> str:
    size_mb = feed.path.stat().st_size / 1e6
    # The checksum proves which exact file a report describes, since feeds aren't committed.
    sha256 = hashlib.sha256(feed.path.read_bytes()).hexdigest()
    rows = [[f, f"{len(df):,}", ", ".join(df.columns)] for f, df in sorted(feed.tables.items())]
    missing = [f for f in OPTIONAL_FILES + FARE_FILES if f not in feed.tables]
    return (f"Zip size: {size_mb:.1f} MB · SHA-256 `{sha256}`\n\n"
            + table(["File", "Rows", "Columns"], rows)
            + f"\n\nNot present: {', '.join(missing) or 'none'}")


def agencies(feed: Feed) -> str:
    agency = feed.get("agency.txt")
    if agency is None:
        return "No agency.txt."
    cols = [c for c in ("agency_id", "agency_name", "agency_timezone", "agency_url")
            if c in agency]
    return table(cols, agency[cols].values.tolist())


def calendars(feed: Feed, today: date) -> str:
    """Informs ADR-0011: have the service calendars expired?"""
    out = []
    calendar = feed.get("calendar.txt")
    if calendar is not None and len(calendar):
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        rows = []
        for _, svc in calendar.iterrows():
            end = pd.to_datetime(svc.get("end_date", ""), format="%Y%m%d", errors="coerce")
            runs = "".join(d[:2].title() if svc.get(d) == "1" else "--" for d in days)
            status = "active" if pd.notna(end) and end.date() >= today else "**expired**"
            rows.append([svc.get("service_id"), svc.get("start_date"), svc.get("end_date"),
                         runs, status])
        out.append(table(["service_id", "start", "end", "days", f"on {today}"], rows))
    else:
        out.append("No calendar.txt rows.")
    dates = feed.get("calendar_dates.txt")
    if dates is not None:
        out.append(f"calendar_dates.txt: {len(dates):,} exceptions "
                   f"(exception_type counts: {dates['exception_type'].value_counts().to_dict()})")
    return "\n\n".join(out)


def stops(feed: Feed) -> str:
    """Informs the import: coordinate quality, stations vs platforms, duplicates."""
    s = feed.get("stops.txt")
    if s is None:
        return "No stops.txt."
    lat = pd.to_numeric(s["stop_lat"], errors="coerce")
    lon = pd.to_numeric(s["stop_lon"], errors="coerce")
    missing = lat.isna() | lon.isna() | ((lat == 0) & (lon == 0))
    outside = ~missing & ~(lat.between(*NCR_LAT) & lon.between(*NCR_LON))
    loc_type = s["location_type"].replace("", "0") if "location_type" in s else None
    with_parent = (s["parent_station"] != "").sum() if "parent_station" in s else 0
    rows = [
        ["Stops", f"{len(s):,}"],
        ["location_type counts", loc_type.value_counts().to_dict() if loc_type is not None
         else "column absent (all treated as stops)"],
        ["With parent_station", f"{with_parent:,}"],
        ["Missing or 0,0 coordinates", pct(int(missing.sum()), len(s))],
        ["Outside Delhi NCR box", pct(int(outside.sum()), len(s))],
        ["Duplicate stop names", (f"{int(s['stop_name'].duplicated(keep=False).sum()):,} stops "
         f"share a name with another stop")],
        ["Exact duplicate coordinates", f"{int(pd.concat([lat, lon], axis=1).duplicated(keep=False).sum()):,} stops"],
    ]
    examples = s.loc[outside, ["stop_id", "stop_name", "stop_lat", "stop_lon"]].head(5)
    text = table(["Check", "Result"], rows)
    if len(examples):
        text += "\n\nExamples outside the box:\n\n" + table(list(examples.columns),
                                                             examples.values.tolist())
    return text


def routes_and_trips(feed: Feed) -> str:
    """Informs ADR-0003: RAPTOR needs one 'route' per distinct stop sequence (pattern)."""
    routes, trips, st = feed.get("routes.txt"), feed.get("trips.txt"), feed.get("stop_times.txt")
    if routes is None or trips is None or st is None:
        return "routes.txt, trips.txt or stop_times.txt missing."
    types = routes["route_type"].map(lambda t: f"{t} ({ROUTE_TYPES.get(t, 'other')})")
    per_route = trips.groupby("route_id").size()
    ordered = st.assign(seq=pd.to_numeric(st["stop_sequence"], errors="coerce"))
    ordered = ordered.sort_values(["trip_id", "seq"])
    patterns = ordered.groupby("trip_id")["stop_id"].agg(tuple)
    trip_patterns = trips.set_index("trip_id")["route_id"].to_frame().join(
        patterns.rename("pattern"), how="inner")
    pattern_count = trip_patterns.drop_duplicates().shape[0]
    patterns_per_route = trip_patterns.drop_duplicates().groupby("route_id").size()
    rows = [
        ["Routes", f"{len(routes):,}"],
        ["route_type", types.value_counts().to_dict()],
        ["Trips", f"{len(trips):,}"],
        ["Trips per route (median / max)", f"{per_route.median():.0f} / {per_route.max():,}"],
        ["Distinct stop patterns (RAPTOR routes)", f"{pattern_count:,}"],
        ["Routes with more than one pattern", f"{int((patterns_per_route > 1).sum()):,}"],
        ["Trips without stop_times", f"{len(set(trips['trip_id']) - set(patterns.index)):,}"],
    ]
    sample = routes.head(5)[[c for c in ("route_id", "route_short_name", "route_long_name",
                                         "route_type") if c in routes]]
    return (table(["Check", "Result"], rows) + "\n\nSample routes:\n\n"
            + table(list(sample.columns), sample.values.tolist()))


def stop_times(feed: Feed) -> str:
    """Informs ADR-0007: are times estimated at constant speed? Also overnight service."""
    st, s = feed.get("stop_times.txt"), feed.get("stops.txt")
    if st is None or s is None:
        return "stop_times.txt or stops.txt missing."
    frame = pd.DataFrame({
        "trip": st["trip_id"],
        "seq": pd.to_numeric(st["stop_sequence"], errors="coerce"),
        "stop": st["stop_id"],
        "arr": gtfs_seconds(st["arrival_time"]),
        "dep": gtfs_seconds(st["departure_time"]),
    }).sort_values(["trip", "seq"])
    coords = s.set_index("stop_id")[["stop_lat", "stop_lon"]].apply(pd.to_numeric,
                                                                     errors="coerce")
    frame = frame.join(coords, on="stop")

    nxt = frame.groupby("trip").shift(-1)
    hops = pd.DataFrame({
        "trip": frame["trip"],
        "secs": nxt["arr"] - frame["dep"],
        "metres": haversine_m(frame["stop_lat"], frame["stop_lon"],
                              nxt["stop_lat"], nxt["stop_lon"]),
        "repeat": frame["stop"] == nxt["stop"],
    }).dropna()
    zero = hops[hops["secs"] <= 0]
    moving = hops[hops["secs"] > 0]
    kmh = moving["metres"] / moving["secs"] * 3.6
    # A coefficient of variation near 0 means every hop in a trip has the same speed,
    # which is what "estimated assuming constant speed" would produce.
    trip_cv = moving.assign(kmh=kmh).groupby("trip")["kmh"].agg(
        lambda v: v.std() / v.mean() if len(v) > 2 and v.mean() > 0 else np.nan).dropna()
    first_dep = frame.groupby("trip")["dep"].min()
    last_arr = frame.groupby("trip")["arr"].max()

    rows = [
        ["stop_times rows", f"{len(frame):,}"],
        ["Blank arrival/departure times", pct(int((frame["arr"].isna() | frame["dep"].isna()).sum()), len(frame))],
        ["Times at or after 24:00 (overnight)", pct(int((frame["dep"] >= 86_400).sum()), len(frame))],
        ["Dwell (departure later than arrival)", pct(int((frame["dep"] > frame["arr"]).sum()), len(frame))],
        ["Hops with zero or negative travel time", pct(len(zero), len(hops))],
        ["  … between identical coordinates", pct(int((zero["metres"] == 0).sum()), len(zero))],
        ["  … same stop listed twice in a row", pct(int(zero["repeat"].sum()), len(zero))],
        ["Hop speed km/h (p5 / median / p95)",
         f"{kmh.quantile(.05):.1f} / {kmh.median():.1f} / {kmh.quantile(.95):.1f}"],
        ["Hops faster than 100 km/h", pct(int((kmh > 100).sum()), len(kmh))],
        ["Per-trip speed variation, median CV", (f"{trip_cv.median():.3f} "
         "(≈0 means constant speed)")],
        ["Trips with CV < 0.05", pct(int((trip_cv < 0.05).sum()), len(trip_cv))],
        ["First departure / last arrival", f"{clock(first_dep.min())} / {clock(last_arr.max())}"],
        ["Trip duration minutes (median / max)",
         f"{((last_arr - first_dep) / 60).median():.0f} / {((last_arr - first_dep) / 60).max():.0f}"],
    ]
    return table(["Check", "Result"], rows)


def fares(feed: Feed) -> str:
    """Informs ADR-0006: can fares come from the feed?"""
    present = [f for f in FARE_FILES if f in feed.tables]
    if not present:
        return "**No fare files.** Fares must come from official tables (ADR-0006)."
    parts = []
    for f in present:
        df = feed.tables[f]
        parts.append(f"`{f}`: {len(df):,} rows\n\n" + table(list(df.columns),
                                                            df.head(5).values.tolist()))
    return "\n\n".join(parts)


def memory_estimate(feed: Feed) -> str:
    """Informs ADR-0009: will the network fit in a small server's memory?"""
    st = feed.get("stop_times.txt")
    if st is None:
        return "n/a"
    # Compact RAPTOR layout: arrival + departure as int32 per stop event, plus a stop index.
    compact_mb = len(st) * (4 + 4 + 4) / 1e6
    # Naive layout: Python objects per stop event (~200 bytes each, an order of magnitude).
    naive_mb = len(st) * 200 / 1e6
    return (f"~{compact_mb:,.0f} MB as compact arrays vs ~{naive_mb:,.0f} MB as Python objects "
            "(order-of-magnitude estimate for stop events only).")


def cross_feed(feeds: list[Feed]) -> str:
    """Informs the transfer-linking stage: how many stops of one feed are walkable from the other?"""
    out = []
    for i, a in enumerate(feeds):
        for b in feeds[i + 1:]:
            stops_a, stops_b = a.get("stops.txt"), b.get("stops.txt")
            if stops_a is None or stops_b is None:
                continue
            clash = set(stops_a["stop_id"]) & set(stops_b["stop_id"])
            out.append(f"stop_id values shared by **{a.name}** and **{b.name}**: {len(clash):,} "
                       "(must be namespaced on import if non-zero)")

            # Measure from the smaller feed (e.g. metro stations) to the larger one, so the
            # full distance matrix stays small enough to compute directly.
            (src_name, src), (dst_name, dst) = sorted(
                [(a.name, stops_a), (b.name, stops_b)], key=lambda pair: len(pair[1]))
            src_lat, src_lon, dst_lat, dst_lon = (
                pd.to_numeric(frame[col], errors="coerce").to_numpy()
                for frame, col in ((src, "stop_lat"), (src, "stop_lon"),
                                   (dst, "stop_lat"), (dst, "stop_lon")))
            dist = haversine_m(src_lat[:, None], src_lon[:, None],
                               dst_lat[None, :], dst_lon[None, :])
            rows = []
            for radius in TRANSFER_RADII_M:
                counts = (dist <= radius).sum(axis=1)
                rows.append([f"{radius} m", pct(int((counts == 0).sum()), len(counts)),
                             f"{np.median(counts):.0f}", f"{counts.max():,}"])
            out.append(f"From each **{src_name}** stop to **{dst_name}** stops:\n\n"
                       + table(["Radius", "With none in range", "Median in range", "Max"], rows))
    return "\n\n".join(out) or "Only one feed given."


# --------------------------------------------------------------------------- report

def report(feeds: list[Feed], today: date) -> str:
    parts = [
        "# GTFS feed inspection",
        (f"Generated by `scripts/inspect_gtfs.py` on {today}. Statistics only; the feeds "
        "themselves are not in this repository (ADR-0011)."),
    ]
    sections = [
        ("Files", inventory), ("Agency", agencies),
        ("Service calendars (ADR-0011)", lambda f: calendars(f, today)),
        ("Stops", stops), ("Routes, trips and RAPTOR patterns (ADR-0003)", routes_and_trips),
        ("Stop times (ADR-0007)", stop_times), ("Fares (ADR-0006)", fares),
        ("Memory (ADR-0009)", memory_estimate),
    ]
    for feed in feeds:
        parts.append(f"## Feed: {feed.name} (`{feed.path.name}`)")
        for title, check in sections:
            parts.append(f"### {title}\n\n{check(feed)}")
    parts.append("## Across feeds (transfer linking)\n\n" + cross_feed(feeds))
    return "\n\n".join(parts) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--feed", action="append", required=True, metavar="NAME=ZIP",
                        help="feed to inspect, e.g. bus=data/raw/dtc-bus.zip (repeatable)")
    parser.add_argument("--out", type=Path, help="write the Markdown report here")
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()

    feeds = []
    for spec in args.feed:
        name, _, path = spec.partition("=")
        feeds.append(load_feed(name, Path(path)))
    text = report(feeds, args.today)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
        print(f"Wrote {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
