"""Small builders for trip-planning test data."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.trips.engine import Itinerary
from app.trips.schemas import Leg, Location, Mode, Route, Stop

DELHI = ZoneInfo("Asia/Kolkata")
START = datetime(2026, 10, 24, 9, 0, tzinfo=DELHI)

ORIGIN = Location(name="Kashmere Gate", lat=28.6675, lon=77.2280)
DESTINATION = Location(name="India Gate", lat=28.6129, lon=77.2295)


def leg(
    mode: Mode,
    start_min: int,
    end_min: int,
    *,
    route: str | None = None,
    distance_m: int = 1_000,
    start: str = "A",
    end: str = "B",
) -> Leg:
    return Leg(
        mode=mode,
        start=Stop(name=start, lat=28.6, lon=77.2),
        end=Stop(name=end, lat=28.61, lon=77.21),
        departure=START + timedelta(minutes=start_min),
        arrival=START + timedelta(minutes=end_min),
        duration_s=(end_min - start_min) * 60,
        distance_m=distance_m,
        route=Route(code=route) if route else None,
        geometry=[(77.2, 28.6), (77.21, 28.61)],
    )


def bus_trip(
    route: str, depart_min: int, arrive_min: int, *, walk_m: int = 300, offset: int = 0
) -> Itinerary:
    """Walk, one bus, walk. `offset` shifts everything, e.g. for later departures."""
    return Itinerary(
        legs=[
            leg("walk", depart_min + offset, depart_min + offset + 3, distance_m=walk_m // 2),
            leg(
                "bus",
                depart_min + offset + 3,
                arrive_min + offset - 3,
                route=route,
                distance_m=5_000,
                start="Stop 1",
                end="Stop 2",
            ),
            leg("walk", arrive_min + offset - 3, arrive_min + offset, distance_m=walk_m // 2),
        ],
        transfers=0,
    )
