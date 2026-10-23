"""Official Delhi fare tables (ADR-0006), as of the dates below. They go stale: re-check
the sources when updating, and change AS_OF.

The bus feed has no fare files, so bus fares come from DTC's distance slabs. Whether a bus
is AC isn't in the feed, so bus fares are a range from non-AC to AC.
"""

import math
from datetime import datetime

from app.trips.schemas import Fare

AS_OF = "2026-10-23"

# DTC and cluster buses: (up to metres, rupees). Long-standing slabs, published by DTC;
# third-party 2026 guides agree (https://buspe.app/guides/delhi-bus-fares-passes).
BUS_NON_AC = ((4_000, 5), (10_000, 10), (math.inf, 15))
BUS_AC = ((4_000, 10), (8_000, 15), (12_000, 20), (math.inf, 25))
BUS_NOTE = "Non-AC to AC fare. Free for women on DTC and cluster buses."

# Auto-rickshaw meter tariff, Delhi Transport Department notification of October 2022:
# ₹30 for the first 1.5 km, then ₹11 per km; 25% extra from 23:00 to 05:00.
# https://www.dnaindia.com/delhi/report-delhi-auto-taxi-fares-hiked-as-govt-notifies-new-rates-delhi-auto-new-fare-check-new-details-3016354
AUTO_BASE, AUTO_BASE_M, AUTO_PER_KM = 30, 1_500, 11
NIGHT_SURCHARGE, NIGHT_START, NIGHT_END = 0.25, 23, 5

# Taxi meter tariff from the same notification: ₹40 for the first km, then ₹17 (non-AC)
# or ₹20 (AC) per km. App cabs set their own, demand-based prices, which aren't public
# (ADR-0004), so the metered tariff is the honest reference point.
TAXI_BASE, TAXI_BASE_M, TAXI_PER_KM_NON_AC, TAXI_PER_KM_AC = 40, 1_000, 17, 20
CAB_NOTE = "Government taxi meter rate. App cab prices vary with demand."


def _slab(table: tuple[tuple[float, int], ...], distance_m: float) -> int:
    return next(price for limit, price in table if distance_m <= limit)


def bus_fare(ride_distances_m: list[float]) -> Fare:
    """One ticket per bus boarded, priced by the distance ridden on that bus."""
    return Fare(
        min=sum(_slab(BUS_NON_AC, d) for d in ride_distances_m),
        max=sum(_slab(BUS_AC, d) for d in ride_distances_m),
        note=BUS_NOTE,
    )


def _metered(base: int, base_m: int, per_km: float, distance_m: float) -> float:
    return base + max(0.0, distance_m - base_m) / 1000 * per_km


def _is_night(at: datetime) -> bool:
    return at.hour >= NIGHT_START or at.hour < NIGHT_END


def auto_fare(distance_m: float, at: datetime) -> Fare:
    fare = _metered(AUTO_BASE, AUTO_BASE_M, AUTO_PER_KM, distance_m)
    if _is_night(at):
        fare *= 1 + NIGHT_SURCHARGE
    amount = math.ceil(fare)
    note = "Meter fare, including the 25% night charge." if _is_night(at) else "Meter fare."
    return Fare(min=amount, max=amount, note=note)


def cab_fare(distance_m: float) -> Fare:
    return Fare(
        min=math.ceil(_metered(TAXI_BASE, TAXI_BASE_M, TAXI_PER_KM_NON_AC, distance_m)),
        max=math.ceil(_metered(TAXI_BASE, TAXI_BASE_M, TAXI_PER_KM_AC, distance_m)),
        note=CAB_NOTE,
    )
