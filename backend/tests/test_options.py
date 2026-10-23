import asyncio
from datetime import datetime, timedelta
from typing import Literal

import pytest

from app.trips import fares
from app.trips.engine import Itinerary, StreetRoute
from app.trips.options import (
    DELHI,
    add_labels,
    in_delhi_time,
    pick_transit,
    plan_trip,
    transit_options,
)
from app.trips.schemas import Location
from tests.factories import DESTINATION, ORIGIN, START, bus_trip, leg


def test_same_bus_later_is_listed_as_a_later_departure() -> None:
    options = transit_options(
        [bus_trip("216", 0, 30), bus_trip("216", 0, 30, offset=6), bus_trip("171", 0, 35)]
    )
    by_title = {o.title: o for o in options}

    assert set(by_title) == {"Bus 216", "Bus 171"}
    assert by_title["Bus 216"].later_departures == [START + timedelta(minutes=6)]


def test_bus_fare_is_charged_per_bus_boarded() -> None:
    two_buses = Itinerary(
        legs=[
            leg("bus", 0, 10, route="1", distance_m=3_000),
            leg("walk", 10, 12),
            leg("bus", 12, 30, route="2", distance_m=9_000, start="C", end="D"),
        ],
        transfers=1,
    )
    [option] = transit_options([two_buses])
    # Non-AC: 5 (≤4 km) + 10 (≤10 km); AC: 10 + 20 (≤12 km).
    assert (option.fare.min, option.fare.max) == (15, 30)
    assert option.title == "Bus 1 + Bus 2"


def test_pick_transit_drops_journeys_worse_on_every_count() -> None:
    options = transit_options(
        [
            bus_trip("fast", 0, 30, walk_m=900),
            bus_trip("slow", 0, 45, walk_m=900),  # later, same walking: dominated
            bus_trip("less-walk", 0, 40, walk_m=100),  # later but walks less: a trade-off
        ]
    )
    assert [o.title for o in pick_transit(options)] == ["Bus fast", "Bus less-walk"]


def test_labels_only_appear_when_they_tell_options_apart() -> None:
    options = transit_options([bus_trip("a", 0, 30, walk_m=900), bus_trip("b", 0, 40, walk_m=100)])
    add_labels(options)
    labels = {o.title: o.labels for o in options}

    assert "fastest" in labels["Bus a"]
    assert "least_walking" in labels["Bus b"]
    # Same fare and same changes for both: no "cheapest" or "fewest changes" label.
    assert not any(label in ("cheapest", "fewest_changes") for o in options for label in o.labels)


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        (datetime(2026, 10, 24, 9, 0), datetime(2026, 10, 24, 9, 0, tzinfo=DELHI)),
        (
            datetime.fromisoformat("2026-10-24T03:30:00+00:00"),
            datetime(2026, 10, 24, 9, 0, tzinfo=DELHI),
        ),
    ],
)
def test_times_are_read_as_delhi_time(given: datetime, expected: datetime) -> None:
    assert in_delhi_time(given) == expected


def test_fares() -> None:
    assert fares.bus_fare([12_500]).model_dump(include={"min", "max"}) == {"min": 15, "max": 25}
    day, night = START, START.replace(hour=23, minute=30)
    assert fares.auto_fare(5_500, day).min == 30 + 44  # 4 km beyond the first 1.5 km
    assert fares.auto_fare(5_500, night).min == 93  # 74 + 25%, rounded up
    assert (fares.cab_fare(5_000).min, fares.cab_fare(5_000).max) == (108, 120)


class FakePlanner:
    def __init__(self, itineraries: list[Itinerary], car_m: int, walk_m: int) -> None:
        self.itineraries, self.car_m, self.walk_m = itineraries, car_m, walk_m

    async def transit(self, origin: Location, destination: Location, depart_at: datetime):
        return self.itineraries

    async def street(self, origin: Location, destination: Location, mode: Literal["walk", "car"]):
        distance = self.car_m if mode == "car" else self.walk_m
        speed = 10 if mode == "car" else 1.3  # metres per second
        return StreetRoute(distance, int(distance / speed), [(77.2, 28.6), (77.21, 28.61)])


def test_plan_adds_auto_and_cab_with_traffic_and_skips_long_walks() -> None:
    planner = FakePlanner([bus_trip("216", 0, 30)], car_m=9_000, walk_m=8_000)
    response = asyncio.run(plan_trip(planner, ORIGIN, DESTINATION, START))
    kinds = {o.kind: o for o in response.options}

    assert set(kinds) == {"transit", "auto", "cab"}  # 8 km is too far to offer walking
    # 9 km at the 09:00 peak speed of 18 km/h is 30 min, slower than the free-flow 15 min.
    assert kinds["auto"].legs[0].duration_s == 30 * 60
    assert kinds["auto"].departure == START + timedelta(minutes=3)  # finding an auto
    assert kinds["cab"].legs[0].times_estimated
    assert response.notices


def test_short_trips_offer_walking_but_no_auto() -> None:
    planner = FakePlanner([], car_m=600, walk_m=550)
    response = asyncio.run(plan_trip(planner, ORIGIN, DESTINATION, START))
    assert [o.kind for o in response.options] == ["walk"]
    assert response.options[0].fare is None
