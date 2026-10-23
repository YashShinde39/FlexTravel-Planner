import csv
import io
import zipfile
from pathlib import Path

import pytest

from app.data import metro_feed, metro_lines, opl
from app.data.metro_lines import Headways, Hours, Line

# A tiny network: the Red Line runs west-east through Hub on a track that bends north, the
# Blue Line runs south-north through Hub. One entrance is mapped at Hub.
OPL = """\
n10 v1 Tname=Alpha x77.00 y28.60
n50 v1 x77.01 y28.61
n11 v1 Tname=Hub%20%(Red%20%Line) x77.02 y28.60
n12 v1 Tname=Gamma x77.04 y28.60
n20 v1 Tname=Delta x77.0201 y28.58
n21 v1 Tname=Hub%20%(Blue%20%Line) x77.0201 y28.6001
n22 v1 Tname=Epsilon x77.0201 y28.62
n90 v1 Trailway=subway_entrance x77.0205 y28.6003
w100 v1 Trailway=subway Nn10,n50,n11,n12
w200 v1 Trailway=subway Nn20,n21,n22
r1 v1 Ttype=route,route=subway,colour=#FF4040 Mn10@stop,n11@stop,n12@stop,w100@
r2 v1 Ttype=route,route=subway Mn12@stop,n11@stop,n10@stop,w100@
r3 v1 Ttype=route,route=subway,colour=gray Mn20@stop,n21@stop,n22@stop,w200@
r4 v1 Ttype=route,route=subway Mn22@stop,n21@stop,n20@stop,w200@
"""

RED = Line(
    id="red",
    name="Red Line",
    agency="dmrc",
    route_type=1,
    relations=(1, 2),
    headways=Headways(peak=4, day=6, late=8, sunday=6),
    hours=Hours(first="05:30", last="23:00", sunday_first="06:00"),
    speed_from="red",
    source="test",
)
BLUE = Line(**{**RED.__dict__, "id": "blue", "name": "Blue Line", "relations": (3, 4)})


@pytest.fixture
def network(monkeypatch: pytest.MonkeyPatch) -> opl.OsmData:
    monkeypatch.setattr(metro_lines, "LINES", (RED, BLUE))
    monkeypatch.setattr(metro_lines, "SPEED_CHECKS", {"red": (10, "test")})
    monkeypatch.setattr(metro_lines, "TIME_REPORTS", {})
    monkeypatch.setattr(metro_lines, "CHANGE_MIN", {"Hub": 6})
    return opl.parse(OPL.splitlines())


def read(feed: Path, name: str) -> list[dict[str, str]]:
    with zipfile.ZipFile(feed) as z:
        return list(csv.DictReader(io.TextIOWrapper(z.open(name), encoding="utf-8")))


def test_opl_reads_tags_positions_ways_and_members() -> None:
    data = opl.parse(OPL.splitlines())
    assert data.node_tags[11]["name"] == "Hub (Red Line)"
    assert data.node_coords[12] == (77.04, 28.60)
    assert data.way_nodes[100] == [10, 50, 11, 12]
    assert [(m.type, m.ref, m.role) for m in data.relation_members[1]][-1] == ("w", 100, "")


def test_distances_follow_the_track_not_a_straight_line(network: opl.OsmData) -> None:
    pattern = metro_feed.build_pattern(network, RED, 1)
    straight = metro_feed.distance_m((77.00, 28.60), (77.02, 28.60))
    # Alpha -> Hub bends north through n50.
    assert pattern.segments_m[0] > straight * 1.3
    assert pattern.straight_segments == 0
    assert pattern.shape[:3] == [(77.00, 28.60), (77.01, 28.61), (77.02, 28.60)]


def test_speed_is_calibrated_to_the_published_time(network: opl.OsmData) -> None:
    patterns = {
        line.id: [metro_feed.build_pattern(network, line, r) for r in line.relations]
        for line in (RED, BLUE)
    }
    speeds = metro_feed.running_speeds(patterns)
    # Red's journey takes the published 10 minutes, and Blue borrows Red's speed.
    assert metro_feed.journey_seconds(patterns["red"][0], speeds["red"]) == pytest.approx(
        600, abs=2
    )
    assert speeds["blue"] == speeds["red"]


def test_frequencies_follow_the_day() -> None:
    weekday = metro_feed.frequency_bands(RED, "weekday")
    assert weekday[0] == (5 * 3600 + 1800, 8 * 3600, 360)  # early morning: daytime frequency
    assert (8 * 3600, 11 * 3600, 240) in weekday  # morning peak
    assert weekday[-1] == (21 * 3600, 23 * 3600 + 60, 480)  # late, including the 23:00 train
    assert metro_feed.frequency_bands(RED, "sunday") == [(6 * 3600, 23 * 3600 + 60, 360)]


def test_feed_models_interchanges_with_walkways(network: opl.OsmData, tmp_path: Path) -> None:
    feed = tmp_path / "metro.gtfs.zip"
    report = metro_feed.generate(network, feed, entrances=[(77.0205, 28.6003)])

    assert (report.stations, report.interchanges, report.modelled_interchanges) == (5, 1, 1)
    stops = {s["stop_id"]: s for s in read(feed, "stops.txt")}
    # "Hub (Red Line)" and "Hub (Blue Line)" are one station with a platform per line.
    assert {"hub", "hub:red", "hub:blue", "hub:entrance-1"} <= set(stops)
    assert stops["hub:red"]["stop_name"] == "Hub" and stops["hub:red"]["parent_station"] == "hub"
    # Changing lines through the entrance takes at least Hub's 6 minutes.
    walkways = {p["to_stop_id"]: int(p["traversal_time"]) for p in read(feed, "pathways.txt")}
    assert walkways["hub:red"] + walkways["hub:blue"] >= 6 * 60
    assert min(walkways.values()) >= 3 * 60

    routes = {r["route_id"]: r for r in read(feed, "routes.txt")}
    assert (routes["red"]["route_color"], routes["red"]["route_text_color"]) == ("FF4040", "FFFFFF")
    assert routes["blue"]["route_color"] == "808080"  # OSM's "gray"

    trips = read(feed, "trips.txt")
    assert {t["trip_headsign"] for t in trips if t["route_id"] == "red"} == {"Gamma", "Alpha"}
    times = [s for s in read(feed, "stop_times.txt") if s["trip_id"] == "red-1-weekday"]
    assert [s["stop_id"] for s in times] == ["alpha:red", "hub:red", "gamma:red"]
    assert times[0]["departure_time"] == "00:00:00"
    assert {f["exact_times"] for f in read(feed, "frequencies.txt")} == {"1"}


def test_interchanges_without_mapped_entrances_are_reported(
    network: opl.OsmData, tmp_path: Path
) -> None:
    report = metro_feed.generate(network, tmp_path / "metro.gtfs.zip")
    assert report.modelled_interchanges == 0
    assert any(w.startswith("Hub: no entrances mapped") for w in report.warnings)
