"""The trip-planning API contract. The frontend's types are generated from these models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Mode = Literal["walk", "bus", "metro", "rail", "auto", "cab"]
OptionKind = Literal["transit", "auto", "cab", "walk"]
OptionLabel = Literal["fastest", "cheapest", "fewest_changes", "least_walking"]


class Location(BaseModel):
    name: str = Field(max_length=200)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class PlanRequest(BaseModel):
    origin: Location
    destination: Location
    # When to leave. Omitted means now. A time without an offset is read as Delhi time.
    depart_at: datetime | None = None


class Stop(BaseModel):
    name: str
    lat: float
    lon: float


class Route(BaseModel):
    code: str  # as printed on the vehicle, e.g. "764M STL"
    agency: str | None = None


class Step(BaseModel):
    """One turn-by-turn instruction on a walk, e.g. "Turn left onto Mori Gate Road"."""

    instruction: str
    distance_m: int


class Leg(BaseModel):
    mode: Mode
    start: Stop
    end: Stop
    departure: datetime
    arrival: datetime
    duration_s: int
    distance_m: int
    route: Route | None = None
    headsign: str | None = None  # which way the vehicle is going: its final stop
    intermediate_stops: list[Stop] = []
    # [lon, lat] pairs, GeoJSON order, ready for the map.
    geometry: list[tuple[float, float]]
    steps: list[Step] = []
    # Bus times in the Delhi feed are estimates from a constant speed (ADR-0007), and
    # auto/cab times are estimated from typical traffic. Shown as "~" in the UI.
    times_estimated: bool = False


class Fare(BaseModel):
    """A fare range in rupees: buses differ for AC and non-AC, cabs vary with demand."""

    min: int
    max: int
    currency: Literal["INR"] = "INR"
    note: str | None = None


class TripOption(BaseModel):
    id: str
    kind: OptionKind
    title: str  # e.g. "Bus 216" or "Auto"
    departure: datetime
    arrival: datetime
    duration_s: int
    transfers: int
    walk_m: int
    fare: Fare | None
    labels: list[OptionLabel] = []
    legs: list[Leg]
    # The same journey on later vehicles, so the list isn't five copies of one bus.
    later_departures: list[datetime] = []


class PlanResponse(BaseModel):
    options: list[TripOption]
    notices: list[str] = []
