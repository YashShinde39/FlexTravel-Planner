"""Clean the DTC/DIMTS bus feed for the routing engine (ADR-0012).

    uv run python -m app.data.bus_feed ../data/raw/dtc-bus-mirror-2023.zip \
        ../data/work/otp/dtc-bus.gtfs.zip

Cleaning steps, each counted in the output so the changes are visible:

1. Calendar: every trip runs every day (ADR-0012), so the single service period is
   extended to cover today and the next years instead of ending in 2024.
2. Consecutive duplicate stop visits are collapsed into one (first arrival, last
   departure). Non-consecutive revisits are real loops and are kept.
3. Routes get a short name as printed on the bus (`764MSTLDOWN` -> `764M STL`) and trips
   get a headsign (their final stop), which the feed leaves empty.
4. ALL-CAPS and all-lowercase stop names are tidied for display ("GOLCHA CINEMA" ->
   "Golcha Cinema"); mixed-case names are left as published.
5. Exact duplicate rows in trips.txt (8 in the 2023 feed) are dropped; GTFS requires
   unique trip IDs and the routing engine rejects the feed otherwise.

The input is never modified; the output is a new GTFS zip in `data/work/` (gitignored).
"""

import argparse
import csv
import io
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from app.data.route_names import display_code

# Kept upper case when tidying ALL-CAPS stop names.
ABBREVIATIONS = {"ISBT", "AIIMS", "NSIC", "CGHS", "NDMC", "DIMTS"}

# Far enough ahead to never expire in practice; the engine only loads a window around today.
SERVICE_END_DATE = "20991231"


@dataclass
class CleaningReport:
    trips: int = 0
    stop_visits_in: int = 0
    duplicate_visits_removed: int = 0
    duplicate_trips_removed: int = 0
    stop_names_tidied: int = 0
    routes_named: int = 0
    headsigns_added: int = 0
    notes: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        lines = [
            f"trips:                       {self.trips:>9,}",
            f"stop visits read:            {self.stop_visits_in:>9,}",
            f"consecutive duplicates gone: {self.duplicate_visits_removed:>9,}",
            f"duplicate trip rows dropped: {self.duplicate_trips_removed:>9,}",
            f"stop names tidied:           {self.stop_names_tidied:>9,}",
            f"routes given a short name:   {self.routes_named:>9,}",
            f"trips given a headsign:      {self.headsigns_added:>9,}",
        ]
        return "\n".join(lines + self.notes)


def tidy_name(name: str) -> str:
    """Fix the feed's ALL-CAPS and all-lowercase names for display.

    "G P O KASMIRI GATE" -> "G P O Kasmiri Gate", "rajinder nagar market" -> "Rajinder Nagar
    Market". In all-caps names, short words and well-known abbreviations (GT, ISBT, AIIMS)
    stay upper case. Mixed-case names are left as they are.
    """
    name = " ".join(name.split())
    if name.isupper():
        return " ".join(
            w if len(w) <= 3 or w in ABBREVIATIONS else w.capitalize() for w in name.split(" ")
        )
    if name.islower():
        return " ".join(w.capitalize() for w in name.split(" "))
    return name


def _read(feed: zipfile.ZipFile, name: str) -> Iterator[dict[str, str]]:
    with feed.open(name) as raw:
        yield from csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig"))


def _write(out: zipfile.ZipFile, name: str, columns: list[str], rows: Iterator[dict]) -> None:
    with out.open(name, "w") as raw, io.TextIOWrapper(raw, encoding="utf-8", newline="") as text:
        writer = csv.DictWriter(text, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def collapse_consecutive_duplicates(
    visits: list[dict[str, str]],
) -> tuple[list[dict[str, str]], int]:
    """Merge back-to-back visits of the same stop: first arrival, last departure.

    `visits` must be one trip's stop times in stop_sequence order. Returns the cleaned list
    and the number of visits removed. A stop that reappears later in the trip is a real
    loop and is kept.
    """
    cleaned: list[dict[str, str]] = []
    for visit in visits:
        if cleaned and cleaned[-1]["stop_id"] == visit["stop_id"]:
            cleaned[-1] = {**cleaned[-1], "departure_time": visit["departure_time"]}
        else:
            cleaned.append(visit)
    return cleaned, len(visits) - len(cleaned)


def _trip_stop_times(feed: zipfile.ZipFile) -> Iterator[list[dict[str, str]]]:
    """Yield each trip's stop times in order. The feed lists every trip's rows together."""
    current: list[dict[str, str]] = []
    for row in _read(feed, "stop_times.txt"):
        if current and row["trip_id"] != current[0]["trip_id"]:
            yield sorted(current, key=lambda r: int(r["stop_sequence"]))
            current = []
        current.append(row)
    if current:
        yield sorted(current, key=lambda r: int(r["stop_sequence"]))


def prepare(source: Path, target: Path) -> CleaningReport:
    report = CleaningReport()
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(".partial")

    with (
        zipfile.ZipFile(source) as feed,
        zipfile.ZipFile(partial, "w", zipfile.ZIP_DEFLATED) as out,
    ):
        stops = list(_read(feed, "stops.txt"))
        for stop in stops:
            tidy = tidy_name(stop["stop_name"])
            if tidy != stop["stop_name"]:
                report.stop_names_tidied += 1
                stop["stop_name"] = tidy
        stop_names = {s["stop_id"]: s["stop_name"] for s in stops}

        # Stop times first: cleaning decides each trip's final stop, i.e. its headsign.
        headsigns: dict[str, str] = {}
        seen_trips: set[str] = set()

        def cleaned_stop_times() -> Iterator[dict[str, str]]:
            for visits in _trip_stop_times(feed):
                trip_id = visits[0]["trip_id"]
                if trip_id in seen_trips:
                    # The streaming grouping relies on each trip's rows being contiguous.
                    raise ValueError(f"stop_times.txt is not grouped by trip ({trip_id})")
                seen_trips.add(trip_id)
                report.stop_visits_in += len(visits)
                cleaned, removed = collapse_consecutive_duplicates(visits)
                report.duplicate_visits_removed += removed
                headsigns[trip_id] = stop_names[cleaned[-1]["stop_id"]]
                yield from cleaned

        _write(
            out,
            "stop_times.txt",
            ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"],
            cleaned_stop_times(),
        )

        def trips() -> Iterator[dict[str, str]]:
            written: dict[str, dict[str, str]] = {}
            for trip in _read(feed, "trips.txt"):
                if (previous := written.get(trip["trip_id"])) is not None:
                    if previous != trip:
                        raise ValueError(f"trip {trip['trip_id']} listed twice with different data")
                    report.duplicate_trips_removed += 1
                    continue
                written[trip["trip_id"]] = trip
                report.trips += 1
                if not trip.get("trip_headsign") and trip["trip_id"] in headsigns:
                    report.headsigns_added += 1
                    trip = {**trip, "trip_headsign": headsigns[trip["trip_id"]]}
                yield trip

        _write(out, "trips.txt", ["route_id", "service_id", "trip_id", "trip_headsign"], trips())

        def routes() -> Iterator[dict[str, str]]:
            for route in _read(feed, "routes.txt"):
                if not route.get("route_short_name"):
                    report.routes_named += 1
                    route = {**route, "route_short_name": display_code(route["route_long_name"])}
                yield route

        _write(
            out,
            "routes.txt",
            ["agency_id", "route_id", "route_short_name", "route_long_name", "route_type"],
            routes(),
        )

        def calendar() -> Iterator[dict[str, str]]:
            for period in _read(feed, "calendar.txt"):
                report.notes.append(
                    f"service {period['service_id']}: "
                    f"{period['start_date']}-{period['end_date']} -> "
                    f"{period['start_date']}-{SERVICE_END_DATE} (ADR-0012: runs every day)"
                )
                yield {**period, "end_date": SERVICE_END_DATE}

        calendar_columns = [
            "service_id",
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
            "start_date",
            "end_date",
        ]
        _write(out, "calendar.txt", calendar_columns, calendar())

        _write(out, "stops.txt", list(stops[0].keys()), iter(stops))
        out.writestr("agency.txt", feed.read("agency.txt"))

    partial.replace(target)  # only a complete file ever appears under the final name
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("source", type=Path, help="raw bus feed zip (data/raw/)")
    parser.add_argument("target", type=Path, help="cleaned feed zip to write (data/work/)")
    args = parser.parse_args()
    print(prepare(args.source, args.target))
    print(f"wrote {args.target}")


if __name__ == "__main__":
    main()
