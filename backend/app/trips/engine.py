"""The seam between trip planning and the routing engine.

OpenTripPlanner sits behind this interface for now (ADR-0014); our own RAPTOR will
implement the same methods later, and nothing else in the app has to change. Engines speak
in our own types (`Leg`, `Location`), never in their native response formats.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Protocol

from app.trips.schemas import Leg, Location, Step


class EngineUnavailableError(Exception):
    """The routing engine can't be reached or failed; the API reports this as a 503."""


@dataclass
class Itinerary:
    """One public-transport journey: walk and ride legs, in order."""

    legs: list[Leg]
    transfers: int


@dataclass
class StreetRoute:
    """A door-to-door route on the street network, used for walking, auto and cab options."""

    distance_m: int
    duration_s: int  # free-flow time from the engine; traffic is applied by the caller
    geometry: list[tuple[float, float]]
    steps: list[Step] = field(default_factory=list)


class TripPlanner(Protocol):
    async def transit(
        self, origin: Location, destination: Location, depart_at: datetime
    ) -> list[Itinerary]:
        """Journeys by public transport and walking, leaving at or after `depart_at`."""
        ...

    async def street(
        self, origin: Location, destination: Location, mode: Literal["walk", "car"]
    ) -> StreetRoute | None:
        """The best street route for `mode`, or None if the places aren't connected."""
        ...
