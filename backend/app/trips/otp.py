"""OpenTripPlanner 2 adapter: our `TripPlanner` interface over OTP's GTFS GraphQL API."""

from datetime import datetime
from typing import Any, Literal

import httpx2

from app.trips import polyline
from app.trips.engine import EngineUnavailableError, Itinerary, StreetRoute
from app.trips.schemas import Leg, Location, Mode, Route, Step, Stop

_PLACE = "name lat lon"
_LEG_FIELDS = f"""
    mode duration distance headsign
    start {{ scheduledTime }} end {{ scheduledTime }}
    from {{ {_PLACE} }} to {{ {_PLACE} }}
    route {{ gtfsId shortName longName color textColor agency {{ name }} }}
    intermediateStops {{ {_PLACE} }}
    legGeometry {{ points }}
    steps {{ distance relativeDirection absoluteDirection streetName bogusName }}
"""

TRANSIT_QUERY = f"""
query Transit($origin: PlanLabeledLocationInput!, $destination: PlanLabeledLocationInput!,
              $dateTime: PlanDateTimeInput, $first: Int) {{
  planConnection(origin: $origin, destination: $destination, dateTime: $dateTime,
                 first: $first) {{
    edges {{ node {{ numberOfTransfers legs {{ {_LEG_FIELDS} }} }} }}
  }}
}}
"""

STREET_QUERY = f"""
query Street($origin: PlanLabeledLocationInput!, $destination: PlanLabeledLocationInput!,
             $modes: PlanModesInput) {{
  planConnection(origin: $origin, destination: $destination, modes: $modes, first: 1) {{
    edges {{ node {{ legs {{ {_LEG_FIELDS} }} }} }}
  }}
}}
"""

NEAREST_STOP_QUERY = """
query Nearest($lat: Float!, $lon: Float!) {
  nearest(lat: $lat, lon: $lon, maxDistance: 1000, filterByPlaceTypes: [STOP], first: 1) {
    edges { node { place { ... on Stop { name lat lon } } } }
  }
}
"""

# OTP mode names -> ours. Delhi has no trams or ferries in the feeds we load; Namo Bharat
# is RAIL.
_MODES: dict[str, Mode] = {"WALK": "walk", "BUS": "bus", "SUBWAY": "metro", "RAIL": "rail"}
# Feeds whose times are estimates: the bus feed's come from a constant speed (ADR-0007),
# the Metro's from published frequencies (ADR-0016). An official feed would get its own id.
_ESTIMATED_FEEDS = {"dtc", "metro"}

_TURNS = {
    "LEFT": "Turn left",
    "RIGHT": "Turn right",
    "SLIGHTLY_LEFT": "Bear left",
    "SLIGHTLY_RIGHT": "Bear right",
    "HARD_LEFT": "Turn sharp left",
    "HARD_RIGHT": "Turn sharp right",
    "CONTINUE": "Continue",
    "UTURN_LEFT": "Make a U-turn",
    "UTURN_RIGHT": "Make a U-turn",
    "CIRCLE_CLOCKWISE": "At the roundabout, continue",
    "CIRCLE_COUNTERCLOCKWISE": "At the roundabout, continue",
}


def _location(location: Location) -> dict[str, Any]:
    return {
        "label": location.name,
        "location": {"coordinate": {"latitude": location.lat, "longitude": location.lon}},
    }


def _stop(place: dict[str, Any]) -> Stop:
    return Stop(name=place["name"], lat=place["lat"], lon=place["lon"])


def step_instruction(step: dict[str, Any]) -> str:
    """'Turn left onto Mori Gate Road'. OTP names unnamed ways "path" or "road" (bogusName)."""
    street = "the path" if step.get("bogusName") else step["streetName"]
    direction = step.get("relativeDirection") or "CONTINUE"
    if direction == "DEPART":
        heading = (step.get("absoluteDirection") or "").lower().replace("_", " ")
        return f"Head {heading} on {street}" if heading else f"Start on {street}"
    return f"{_TURNS.get(direction, 'Continue')} onto {street}"


def map_leg(raw: dict[str, Any]) -> Leg:
    mode = _MODES.get(raw["mode"], "walk")
    route = raw.get("route")
    return Leg(
        mode=mode,
        start=_stop(raw["from"]),
        end=_stop(raw["to"]),
        departure=datetime.fromisoformat(raw["start"]["scheduledTime"]),
        arrival=datetime.fromisoformat(raw["end"]["scheduledTime"]),
        duration_s=round(raw["duration"]),
        distance_m=round(raw["distance"]),
        route=(
            Route(
                code=route["shortName"] or route["longName"],
                agency=route["agency"]["name"],
                color=route.get("color"),
                text_color=route.get("textColor"),
            )
            if route
            else None
        ),
        headsign=raw.get("headsign"),
        intermediate_stops=[_stop(s) for s in raw.get("intermediateStops") or []],
        geometry=polyline.decode(raw["legGeometry"]["points"]),
        steps=[
            Step(instruction=step_instruction(s), distance_m=round(s["distance"]))
            for s in raw.get("steps") or []
        ],
        times_estimated=bool(route) and route["gtfsId"].split(":")[0] in _ESTIMATED_FEEDS,
    )


class OtpPlanner:
    def __init__(self, client: httpx2.AsyncClient, base_url: str) -> None:
        self._client = client
        self._url = f"{base_url.rstrip('/')}/otp/gtfs/v1"

    async def _query(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        """Run a GraphQL query and return its single top-level field."""
        try:
            response = await self._client.post(
                self._url, json={"query": query, "variables": variables}, timeout=15
            )
            response.raise_for_status()
            body = response.json()
        except (httpx2.HTTPError, ValueError) as error:
            raise EngineUnavailableError(f"OpenTripPlanner request failed: {error}") from error
        if body.get("errors"):
            raise EngineUnavailableError(f"OpenTripPlanner query error: {body['errors']}")
        return next(iter(body["data"].values()))

    async def transit(
        self, origin: Location, destination: Location, depart_at: datetime
    ) -> list[Itinerary]:
        result = await self._query(
            TRANSIT_QUERY,
            {
                "origin": _location(origin),
                "destination": _location(destination),
                "dateTime": {"earliestDeparture": depart_at.isoformat()},
                "first": 12,  # enough to see repeats of the same bus and real alternatives
            },
        )
        itineraries = []
        for edge in result["edges"]:
            legs = [map_leg(leg) for leg in edge["node"]["legs"]]
            # OTP also returns walk-only journeys; walking is offered as its own option.
            if any(leg.mode != "walk" for leg in legs):
                itineraries.append(Itinerary(legs, edge["node"]["numberOfTransfers"]))
        return itineraries

    async def street(
        self, origin: Location, destination: Location, mode: Literal["walk", "car"]
    ) -> StreetRoute | None:
        route = await self._street(origin, destination, mode)
        if route is None and mode == "car":
            # A place inside a car-free area (India Gate's lawns, a market lane) has no car
            # route. An auto or cab stops at the nearest road instead, and bus stops are
            # always on one.
            route = await self._street(
                await self._nearest_stop(origin), await self._nearest_stop(destination), mode
            )
        return route

    async def _nearest_stop(self, location: Location) -> Location:
        result = await self._query(NEAREST_STOP_QUERY, {"lat": location.lat, "lon": location.lon})
        if not result["edges"]:
            return location
        stop = result["edges"][0]["node"]["place"]
        return Location(name=stop["name"], lat=stop["lat"], lon=stop["lon"])

    async def _street(
        self, origin: Location, destination: Location, mode: Literal["walk", "car"]
    ) -> StreetRoute | None:
        result = await self._query(
            STREET_QUERY,
            {
                "origin": _location(origin),
                "destination": _location(destination),
                "modes": {"directOnly": True, "direct": [mode.upper()]},
            },
        )
        if not result["edges"]:
            return None
        legs = [map_leg(leg) for leg in result["edges"][0]["node"]["legs"]]
        return StreetRoute(
            distance_m=sum(leg.distance_m for leg in legs),
            duration_s=sum(leg.duration_s for leg in legs),
            geometry=[point for leg in legs for point in leg.geometry],
            steps=[step for leg in legs for step in leg.steps],
        )
