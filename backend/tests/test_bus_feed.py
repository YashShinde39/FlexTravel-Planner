import csv
import io
import zipfile
from pathlib import Path

import pytest

from app.data.bus_feed import collapse_consecutive_duplicates, prepare, tidy_name
from app.data.route_names import display_code


@pytest.mark.parametrize(
    ("long_name", "printed"),
    [
        ("764MSTLDOWN", "764M STL"),
        ("511ALNKSTLUP", "511A LNK STL"),
        ("138UP", "138"),
        ("764EXTDOWN", "764 EXT"),
        ("405LSTLUP", "405L STL"),
        ("044(NS)DOWN", "044 (NS)"),
        ("STLDOWN2", "STL2"),  # no route number: only the direction goes
        ("TMS(+)UP", "TMS(+)"),
        ("GL-23(NS)UP", "GL-23 (NS)"),
    ],
)
def test_display_code_matches_what_is_printed_on_the_bus(long_name: str, printed: str) -> None:
    assert display_code(long_name) == printed


@pytest.mark.parametrize(
    ("raw", "tidy"),
    [
        ("GOLCHA CINEMA", "Golcha Cinema"),
        ("G P O KASMIRI GATE", "G P O Kasmiri Gate"),
        ("ISBT KASHMERE GATE", "ISBT Kashmere Gate"),
        ("rajinder nagar market", "Rajinder Nagar Market"),
        ("Hanuman Mandir / Shivaji Stadium", "Hanuman Mandir / Shivaji Stadium"),
        ("  Extra   spaces ", "Extra spaces"),
    ],
)
def test_tidy_name(raw: str, tidy: str) -> None:
    assert tidy_name(raw) == tidy


def visit(stop: str, seq: int, arrival: str, departure: str | None = None) -> dict[str, str]:
    return {
        "trip_id": "t",
        "stop_id": stop,
        "stop_sequence": str(seq),
        "arrival_time": arrival,
        "departure_time": departure or arrival,
    }


def test_consecutive_duplicates_collapse_but_loops_stay() -> None:
    visits = [
        visit("A", 0, "08:00:00"),
        visit("B", 1, "08:05:00"),
        visit("B", 2, "08:05:00", "08:06:00"),  # listed twice in a row: one visit
        visit("C", 3, "08:10:00"),
        visit("A", 4, "08:20:00"),  # back to A later: a real loop
    ]
    cleaned, removed = collapse_consecutive_duplicates(visits)

    assert removed == 1
    assert [v["stop_id"] for v in cleaned] == ["A", "B", "C", "A"]
    # The merged visit arrives at the first time and leaves at the last.
    assert (cleaned[1]["arrival_time"], cleaned[1]["departure_time"]) == ("08:05:00", "08:06:00")


def write_feed(path: Path, files: dict[str, str]) -> None:
    with zipfile.ZipFile(path, "w") as feed:
        for name, content in files.items():
            feed.writestr(name, content.strip() + "\n")


def read_csv(path: Path, name: str) -> list[dict[str, str]]:
    with zipfile.ZipFile(path) as feed:
        return list(csv.DictReader(io.TextIOWrapper(feed.open(name), encoding="utf-8")))


def test_prepare_cleans_a_small_feed(tmp_path: Path) -> None:
    source, target = tmp_path / "raw.zip", tmp_path / "out" / "clean.gtfs.zip"
    write_feed(
        source,
        {
            "agency.txt": "agency_id,agency_name,agency_url,agency_timezone\n"
            "DTC,Delhi Transport Corporation,http://dtc.delhi.gov.in/,Asia/Kolkata",
            "calendar.txt": "start_date,end_date,monday,tuesday,wednesday,thursday,friday,"
            "saturday,sunday,service_id\n20220101,20240101,1,1,1,1,1,1,1,1",
            "routes.txt": "agency_id,route_id,route_long_name,route_short_name,route_type\n"
            "DTC,0,764MSTLDOWN,,3",
            "stops.txt": "stop_id,stop_code,stop_name,stop_lat,stop_lon,zone_id\n"
            "1,X1,NARELA TERMINAL,28.85,77.08,0\n2,X2,Police Station,28.86,77.09,1",
            "trips.txt": "route_id,service_id,trip_id,shape_id\n0,1,t1,\n0,1,t1,\n0,1,t2,",
            "stop_times.txt": "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
            "t1,08:00:00,08:00:00,1,0\nt1,08:05:00,08:05:00,2,1\nt1,08:05:00,08:05:00,2,2\n"
            "t2,09:00:00,09:00:00,2,0\nt2,09:05:00,09:05:00,1,1",
        },
    )

    report = prepare(source, target)

    assert (report.trips, report.duplicate_trips_removed) == (2, 1)
    assert report.duplicate_visits_removed == 1
    assert report.stop_names_tidied == 1
    assert read_csv(target, "calendar.txt")[0]["end_date"] == "20991231"
    assert read_csv(target, "routes.txt")[0]["route_short_name"] == "764M STL"
    headsigns = {t["trip_id"]: t["trip_headsign"] for t in read_csv(target, "trips.txt")}
    assert headsigns == {"t1": "Police Station", "t2": "Narela Terminal"}
    assert len(read_csv(target, "stop_times.txt")) == 4
    assert not target.with_suffix(".partial").exists()


def test_prepare_rejects_conflicting_duplicate_trips(tmp_path: Path) -> None:
    source = tmp_path / "raw.zip"
    write_feed(
        source,
        {
            "agency.txt": "agency_id,agency_name,agency_url,agency_timezone\nA,A,http://a,UTC",
            "calendar.txt": "service_id,start_date,end_date\n1,20220101,20240101",
            "routes.txt": "agency_id,route_id,route_long_name,route_short_name,route_type\n"
            "A,0,1UP,,3\nA,9,2UP,,3",
            "stops.txt": "stop_id,stop_name,stop_lat,stop_lon\n1,One,0,0",
            "trips.txt": "route_id,service_id,trip_id\n0,1,t1\n9,1,t1",
            "stop_times.txt": "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
            "t1,08:00:00,08:00:00,1,0",
        },
    )
    with pytest.raises(ValueError, match="different data"):
        prepare(source, tmp_path / "out.zip")
