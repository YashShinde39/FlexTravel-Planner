import asyncio
import json
from typing import Any

import httpx2
import pytest

from app.trips import polyline
from app.trips.engine import EngineUnavailableError
from app.trips.otp import OtpPlanner, step_instruction
from tests.factories import DESTINATION, ORIGIN, START


def test_polyline_decodes_googles_reference_example() -> None:
    # https://developers.google.com/maps/documentation/utilities/polylinealgorithm
    assert polyline.decode("_p~iF~ps|U_ulLnnqC_mqNvxq`@") == [
        (-120.2, 38.5),
        (-120.95, 40.7),
        (-126.453, 43.252),
    ]


@pytest.mark.parametrize(
    ("step", "text"),
    [
        (
            {
                "relativeDirection": "DEPART",
                "absoluteDirection": "NORTH_EAST",
                "streetName": "Gokhale Road",
            },
            "Head north east on Gokhale Road",
        ),
        (
            {"relativeDirection": "LEFT", "streetName": "Mori Gate Road"},
            "Turn left onto Mori Gate Road",
        ),
        (
            {"relativeDirection": "RIGHT", "streetName": "road", "bogusName": True},
            "Turn right onto the path",
        ),
    ],
)
def test_step_instructions(step: dict[str, Any], text: str) -> None:
    assert step_instruction(step) == text


def otp_leg(mode: str, start: str, end: str, **extra: Any) -> dict[str, Any]:
    return {
        "mode": mode,
        "duration": 600.0,
        "distance": 1234.5,
        "headsign": None,
        "start": {"scheduledTime": start},
        "end": {"scheduledTime": end},
        "from": {"name": "A", "lat": 28.6, "lon": 77.2},
        "to": {"name": "B", "lat": 28.61, "lon": 77.21},
        "route": None,
        "intermediateStops": None,
        "legGeometry": {"points": "_p~iF~ps|U_ulLnnqC"},
        "steps": [],
        **extra,
    }


def planner_returning(*responses: dict[str, Any]) -> tuple[OtpPlanner, list[dict]]:
    """An OtpPlanner whose HTTP calls get `responses` in order; also returns the requests."""
    requests: list[dict] = []
    queue = list(responses)

    def handle(request: httpx2.Request) -> httpx2.Response:
        requests.append(json.loads(request.content))
        return httpx2.Response(200, json=queue.pop(0))

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(handle))
    return OtpPlanner(client, "http://otp:8080/"), requests


def plan_result(*legs_per_itinerary: list[dict[str, Any]]) -> dict[str, Any]:
    edges = [{"node": {"numberOfTransfers": 0, "legs": legs}} for legs in legs_per_itinerary]
    return {"data": {"planConnection": {"edges": edges}}}


def test_transit_maps_legs_and_drops_walk_only_journeys() -> None:
    bus = otp_leg(
        "BUS",
        "2026-10-24T09:04:00+05:30",
        "2026-10-24T09:24:00+05:30",
        headsign="Shivaji Stadium Terminal",
        route={
            "gtfsId": "dtc:216UP",
            "shortName": "216",
            "longName": "216UP",
            "agency": {"name": "DTC"},
        },
        intermediateStops=[{"name": "Mid", "lat": 28.605, "lon": 77.205}],
    )
    walk = otp_leg("WALK", "2026-10-24T09:00:00+05:30", "2026-10-24T09:04:00+05:30")
    planner, requests = planner_returning(plan_result([walk, bus], [walk]))

    [itinerary] = asyncio.run(planner.transit(ORIGIN, DESTINATION, START))

    assert [leg.mode for leg in itinerary.legs] == ["walk", "bus"]
    ride = itinerary.legs[1]
    assert ride.route.code == "216" and ride.headsign == "Shivaji Stadium Terminal"
    assert ride.times_estimated and not itinerary.legs[0].times_estimated
    assert ride.departure.isoformat() == "2026-10-24T09:04:00+05:30"
    assert ride.geometry == [(-120.2, 38.5), (-120.95, 40.7)]
    assert ride.distance_m == 1234 and [s.name for s in ride.intermediate_stops] == ["Mid"]
    assert requests[0]["variables"]["dateTime"] == {"earliestDeparture": START.isoformat()}


def metro_leg(gtfs_id: str) -> dict[str, Any]:
    return otp_leg(
        "SUBWAY",
        "2026-10-24T09:04:00+05:30",
        "2026-10-24T09:24:00+05:30",
        route={
            "gtfsId": gtfs_id,
            "shortName": "Yellow Line",
            "longName": "Samaypur Badli – Millennium City Centre Gurugram",
            "color": "FFDF00",
            "textColor": "000000",
            "agency": {"name": "Delhi Metro"},
        },
    )


def test_metro_legs_carry_the_line_colour_and_are_estimated_until_official() -> None:
    planner, _ = planner_returning(plan_result([metro_leg("metro:yellow")]))
    [itinerary] = asyncio.run(planner.transit(ORIGIN, DESTINATION, START))
    [ride] = itinerary.legs
    assert ride.mode == "metro" and ride.route.code == "Yellow Line"
    assert (ride.route.color, ride.route.text_color) == ("FFDF00", "000000")
    assert ride.times_estimated  # our generated timetable (ADR-0016)

    # An official feed, loaded under its own id, has real times.
    planner, _ = planner_returning(plan_result([metro_leg("dmrc:yellow")]))
    [itinerary] = asyncio.run(planner.transit(ORIGIN, DESTINATION, START))
    assert not itinerary.legs[0].times_estimated


def test_car_route_falls_back_to_nearest_stops_in_car_free_areas() -> None:
    nearest = {
        "data": {
            "nearest": {
                "edges": [
                    {"node": {"place": {"name": "India Gate", "lat": 28.6145, "lon": 77.2277}}}
                ]
            }
        }
    }
    car = otp_leg("CAR", "2026-10-24T09:00:00+05:30", "2026-10-24T09:08:00+05:30")
    planner, requests = planner_returning(
        plan_result(),
        nearest,
        nearest,
        plan_result([car]),  # first try: no route
    )

    route = asyncio.run(planner.street(ORIGIN, DESTINATION, "car"))

    assert route is not None and route.distance_m == 1234
    retried = requests[-1]["variables"]["destination"]["location"]["coordinate"]
    assert retried == {"latitude": 28.6145, "longitude": 77.2277}


@pytest.mark.parametrize(
    "response",
    [httpx2.Response(502), httpx2.Response(200, json={"errors": [{"message": "bad"}]})],
)
def test_engine_failures_become_engine_unavailable(response: httpx2.Response) -> None:
    client = httpx2.AsyncClient(transport=httpx2.MockTransport(lambda _: response))
    with pytest.raises(EngineUnavailableError):
        asyncio.run(OtpPlanner(client, "http://otp").transit(ORIGIN, DESTINATION, START))
