"""Turn engine results into the options a traveller chooses between.

Engine-independent: whichever `TripPlanner` runs underneath, this adds the parts that
are about the product rather than the search: fares, auto and cab estimates, grouping
repeated departures of the same bus, and the "fastest" / "cheapest" labels.
"""

import asyncio
import hashlib
from collections.abc import Iterable
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.trips import fares
from app.trips.engine import Itinerary, StreetRoute, TripPlanner
from app.trips.schemas import (
    Fare,
    Leg,
    Location,
    OptionKind,
    OptionLabel,
    PlanResponse,
    Stop,
    TripOption,
)

DELHI = ZoneInfo("Asia/Kolkata")

# Walking is offered as an option of its own up to this distance.
MAX_WALK_OPTION_M = 3_000
# Below this an auto or cab isn't worth suggesting.
MIN_RIDE_M = 800
# How many later departures of the same journey to list ("also at 09:10, 09:16").
MAX_LATER_DEPARTURES = 3
# Public-transport options shown at most, after removing the clearly worse ones.
MAX_TRANSIT_OPTIONS = 5
# Differences too small to matter when comparing two journeys.
SAME_ARRIVAL = timedelta(minutes=2)
SAME_WALK_M = 200

# The engine routes cars on empty roads. Delhi traffic is much slower, so auto and cab
# times use typical average speeds by time of day instead (whichever is slower). These are
# rough, deliberately conservative assumptions; the UI marks the times as estimates.
PEAK_HOURS = {8, 9, 10, 17, 18, 19, 20}
NIGHT_HOURS = {23, 0, 1, 2, 3, 4, 5}
SPEED_KMH = {"peak": 18, "night": 35, "day": 25}
# Time to find an auto at a stand or for a booked cab to arrive.
WAIT = {"auto": timedelta(minutes=3), "cab": timedelta(minutes=6)}

NOTICES = [
    "Bus times are estimates from the 2023 timetable (the latest published).",
    "Metro and Namo Bharat times are estimates from published frequencies: their "
    "official timetables can't be downloaded at the moment.",
]

RAPID_METRO_AGENCY = "Rapid Metro Gurgaon"


def in_delhi_time(depart_at: datetime | None) -> datetime:
    """Now if not given; a time without an offset is read as Delhi time."""
    if depart_at is None:
        return datetime.now(DELHI).replace(microsecond=0)
    if depart_at.tzinfo is None:
        return depart_at.replace(tzinfo=DELHI)
    return depart_at.astimezone(DELHI)


def _option_id(*parts: object) -> str:
    return hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:12]


def _journey_key(itinerary: Itinerary) -> tuple:
    """Same vehicles between the same stops = same journey, whatever the departure time."""
    return tuple(
        (leg.mode, leg.route.code if leg.route else None, leg.start.name, leg.end.name)
        for leg in itinerary.legs
        if leg.mode != "walk"
    )


def _ride_title(leg: Leg) -> str:
    """A ride's name in titles: "Bus 270", or a Metro line's name, e.g. "Yellow Line"."""
    if leg.route is None:
        return leg.mode.capitalize()
    return f"Bus {leg.route.code}" if leg.mode == "bus" else leg.route.code


def transit_fare(rides: list[Leg]) -> Fare | None:
    """The fare for a journey's rides: one ticket per bus; one per Metro journey, so
    changing lines inside a station adds nothing; Rapid Metro and Namo Bharat separately.
    None if a ride can't be priced."""
    parts: list[Fare] = []
    metro_m = 0.0  # length of the Metro journey in progress
    for index, ride in enumerate(rides):
        next_ride = rides[index + 1] if index + 1 < len(rides) else None
        if ride.mode == "bus":
            parts.append(fares.bus_fare([ride.distance_m]))
        elif ride.mode == "rail":
            parts.append(fares.namo_bharat_fare(ride.distance_m))
        elif ride.mode == "metro" and ride.route and ride.route.agency == RAPID_METRO_AGENCY:
            parts.append(fares.rapid_metro_fare())
        elif ride.mode == "metro":
            metro_m += ride.distance_m
            # The journey continues if the next ride is another Delhi Metro line boarded in
            # the same station; otherwise the traveller leaves the station here.
            continues = (
                next_ride is not None
                and next_ride.mode == "metro"
                and next_ride.route is not None
                and next_ride.route.agency != RAPID_METRO_AGENCY
                and next_ride.start.name == ride.end.name
            )
            if not continues:
                parts.append(fares.metro_fare(metro_m, ride.departure))
                metro_m = 0.0
        else:
            return None
    return fares.combine(parts) if parts else None


def transit_options(itineraries: Iterable[Itinerary]) -> list[TripOption]:
    groups: dict[tuple, list[Itinerary]] = {}
    for itinerary in sorted(itineraries, key=lambda i: i.legs[-1].arrival):
        groups.setdefault(_journey_key(itinerary), []).append(itinerary)

    options = []
    for key, group in groups.items():
        first, later = group[0], group[1:]
        rides = [leg for leg in first.legs if leg.mode != "walk"]
        title = " + ".join(_ride_title(leg) for leg in rides)
        options.append(
            TripOption(
                id=_option_id(key, first.legs[0].departure),
                kind="transit",
                title=title,
                departure=first.legs[0].departure,
                arrival=first.legs[-1].arrival,
                duration_s=int((first.legs[-1].arrival - first.legs[0].departure).total_seconds()),
                transfers=first.transfers,
                walk_m=sum(leg.distance_m for leg in first.legs if leg.mode == "walk"),
                fare=transit_fare(rides),
                legs=first.legs,
                later_departures=[i.legs[0].departure for i in later[:MAX_LATER_DEPARTURES]],
            )
        )
    return options


def _worse_or_equal(a: TripOption, b: TripOption) -> bool:
    """True if `a` is no better than `b` on any count: arrival, changes, walking, fare."""
    return (
        a.arrival >= b.arrival - SAME_ARRIVAL
        and a.transfers >= b.transfers
        and a.walk_m >= b.walk_m - SAME_WALK_M
        and (a.fare.min if a.fare else 0) >= (b.fare.min if b.fare else 0)
    )


def pick_transit(options: list[TripOption]) -> list[TripOption]:
    """Keep journeys that are better than every other on at least one count (Pareto).

    The engine returns many near-copies ("bus 405 then walk" vs "bus 405L then walk", two
    minutes apart). Showing all of them hides the real choice, which is the trade-off
    between arriving earlier, changing less, walking less and paying less.
    """
    kept = [
        option
        for option in options
        if not any(
            other is not option
            and _worse_or_equal(option, other)
            and not _worse_or_equal(other, option)  # exact ties: keep both, cap decides
            for other in options
        )
    ]
    return sorted(kept, key=lambda o: o.arrival)[:MAX_TRANSIT_OPTIONS]


def _road_duration(route: StreetRoute, at: datetime) -> timedelta:
    hour = at.hour
    period = "peak" if hour in PEAK_HOURS else "night" if hour in NIGHT_HOURS else "day"
    traffic_s = route.distance_m / 1000 / SPEED_KMH[period] * 3600
    return timedelta(seconds=round(max(route.duration_s, traffic_s) / 60) * 60)


def street_option(
    kind: OptionKind,
    route: StreetRoute,
    origin: Location,
    destination: Location,
    depart_at: datetime,
) -> TripOption:
    if kind == "walk":
        start, duration = depart_at, timedelta(seconds=route.duration_s)
        fare = None
    else:
        start, duration = depart_at + WAIT[kind], _road_duration(route, depart_at)
        fare = (
            fares.auto_fare(route.distance_m, start)
            if kind == "auto"
            else fares.cab_fare(route.distance_m)
        )
    end = start + duration
    leg = Leg(
        mode=kind,
        start=Stop(name=origin.name, lat=origin.lat, lon=origin.lon),
        end=Stop(name=destination.name, lat=destination.lat, lon=destination.lon),
        departure=start,
        arrival=end,
        duration_s=int(duration.total_seconds()),
        distance_m=route.distance_m,
        geometry=route.geometry,
        steps=route.steps if kind == "walk" else [],
        times_estimated=kind != "walk",
    )
    return TripOption(
        id=_option_id(kind, origin, destination, start),
        kind=kind,
        title=kind.capitalize(),
        departure=start,
        arrival=end,
        duration_s=int((end - depart_at).total_seconds()),
        transfers=0,
        walk_m=route.distance_m if kind == "walk" else 0,
        fare=fare,
        legs=[leg],
    )


def add_labels(options: list[TripOption]) -> None:
    """Mark the best option on each count. A label is only shown when it tells options apart."""
    if len(options) < 2:
        return

    def mark(label: OptionLabel, candidates: list[TripOption], value) -> None:
        if len({value(o) for o in candidates}) < 2:
            return  # all equal (or fewer than two): the label would say nothing
        # Ties go to the earlier arrival.
        min(candidates, key=lambda o: (value(o), o.arrival)).labels.append(label)

    mark("fastest", options, lambda o: o.arrival)
    # Walking is free; "cheapest" compares the options that cost something.
    mark("cheapest", [o for o in options if o.fare], lambda o: o.fare.min)
    transit = [o for o in options if o.kind == "transit"]
    mark("fewest_changes", transit, lambda o: o.transfers)
    mark("least_walking", transit, lambda o: o.walk_m)


async def plan_trip(
    planner: TripPlanner, origin: Location, destination: Location, depart_at: datetime | None
) -> PlanResponse:
    depart_at = in_delhi_time(depart_at)
    itineraries, car, walk = await asyncio.gather(
        planner.transit(origin, destination, depart_at),
        planner.street(origin, destination, "car"),
        planner.street(origin, destination, "walk"),
    )

    options = pick_transit(transit_options(itineraries))
    if car and car.distance_m >= MIN_RIDE_M:
        options.append(street_option("auto", car, origin, destination, depart_at))
        options.append(street_option("cab", car, origin, destination, depart_at))
    if walk and (walk.distance_m <= MAX_WALK_OPTION_M or not options):
        options.append(street_option("walk", walk, origin, destination, depart_at))

    options.sort(key=lambda o: o.arrival)
    add_labels(options)
    return PlanResponse(options=options, notices=NOTICES)
