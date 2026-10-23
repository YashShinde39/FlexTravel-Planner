"""The places and trip-planning endpoints, against the test database and a fake engine."""

import asyncio
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings
from app.data.import_places import Place, replace_places
from app.main import create_app
from app.trips.engine import EngineUnavailableError
from tests.factories import bus_trip
from tests.test_options import FakePlanner

PLACES = [
    Place("osm:n1", "Rajiv Chowk", "metro_station", "Metro station", 28.6328, 77.2197),
    Place("bus:dtc:1", "Rajiv Nagar", "bus_stop", "Bus stop", 28.70, 77.10),
    Place("bus:dtc:2", "AIIMS", "bus_stop", "Bus stop", 28.567, 77.210),
    Place("bus:dtc:3", "AIIMS", "bus_stop", "Bus stop", 28.575, 77.210),  # 900 m away
    Place("bus:dtc:4", "IIT Gate", "bus_stop", "Bus stop", 28.545, 77.192),
]


@pytest.fixture
def api(database_url: str) -> Iterator[TestClient]:
    asyncio.run(replace_places(database_url, PLACES))
    settings = Settings(environment="test", database_url=database_url, photon_url="")
    planner = FakePlanner([bus_trip("216", 0, 30)], car_m=7_000, walk_m=6_000)
    with TestClient(create_app(settings, planner=planner)) as client:
        yield client
    asyncio.run(_clear(database_url))


async def _clear(database_url: str) -> None:
    await replace_places(database_url, [])
    await create_async_engine(database_url).dispose()


def names(response) -> list[str]:
    assert response.status_code == 200, response.text
    return [place["name"] for place in response.json()["places"]]


def test_search_prefers_prefix_matches_and_stations(api: TestClient) -> None:
    assert names(api.get("/api/v1/places", params={"q": "rajiv"})) == [
        "Rajiv Chowk",
        "Rajiv Nagar",
    ]


def test_search_tolerates_typos(api: TestClient) -> None:
    assert names(api.get("/api/v1/places", params={"q": "rajiv chok"}))[0] == "Rajiv Chowk"


def test_search_lists_a_repeated_stop_name_once(api: TestClient) -> None:
    assert names(api.get("/api/v1/places", params={"q": "aiims"})) == ["AIIMS"]


def test_search_needs_two_characters(api: TestClient) -> None:
    assert api.get("/api/v1/places", params={"q": "r"}).status_code == 422


def test_plan_returns_options(api: TestClient) -> None:
    response = api.post(
        "/api/v1/trips/plan",
        json={
            "origin": {"name": "Kashmere Gate", "lat": 28.6675, "lon": 77.2280},
            "destination": {"name": "India Gate", "lat": 28.6129, "lon": 77.2295},
            "depart_at": "2026-10-24T09:00:00",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert {o["kind"] for o in body["options"]} == {"transit", "auto", "cab"}
    bus = next(o for o in body["options"] if o["kind"] == "transit")
    assert bus["legs"][1]["route"]["code"] == "216"
    assert bus["departure"] == "2026-10-24T09:00:00+05:30"


def test_plan_reports_engine_outage_as_503(database_url: str) -> None:
    class DownPlanner(FakePlanner):
        async def transit(self, *args):
            raise EngineUnavailableError("connection refused")

    settings = Settings(environment="test", database_url=database_url, photon_url="")
    app = create_app(settings, planner=DownPlanner([], 0, 0))
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/trips/plan",
            json={
                "origin": {"name": "A", "lat": 28.6, "lon": 77.2},
                "destination": {"name": "B", "lat": 28.7, "lon": 77.3},
            },
        )
    assert response.status_code == 503
    assert "isn't available" in response.json()["detail"]
