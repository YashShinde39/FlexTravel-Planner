"""Official Delhi fare tables (ADR-0006), as of the dates below. They go stale: re-check
the sources when updating, and change AS_OF.

The bus feed has no fare files, so bus fares come from DTC's distance slabs. Whether a bus
is AC isn't in the feed, so bus fares are a range from non-AC to AC. Metro fares come
from the Delhi Metro's distance slabs; Rapid Metro and Namo Bharat are priced separately.
"""

import math
from datetime import datetime

from app.trips.schemas import Fare

AS_OF = "2026-10-24"

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


# Delhi Metro, from 25 August 2025: (up to metres, rupees), and cheaper slabs on Sundays and
# national holidays. Smart cards take 10% off (another 10% off-peak).
# https://www.theweek.in/news/india/2025/08/25/delhi-metro-fare-hike-minimum-ticket-price-now-is-11-check-full-details-here.amp.html
METRO = ((2_000, 11), (5_000, 21), (12_000, 32), (21_000, 43), (32_000, 54), (math.inf, 64))
METRO_SUNDAY = (
    (2_000, 11),
    (5_000, 11),
    (12_000, 21),
    (21_000, 32),
    (32_000, 43),
    (math.inf, 54),
)
METRO_NOTE = "Metro token fare; smart cards save 10%."

# Rapid Metro Gurgaon: ₹20 for one station up to ₹35 for the whole loop (Godrej Properties
# guide, January 2025). Not part of the Delhi Metro fare.
RAPID_METRO = (20, 35)
RAPID_METRO_NOTE = "Rapid Metro is a separate ticket."

# Namo Bharat, standard coach: about ₹2.7 per km (Anand Vihar - Meerut South ₹130, New
# Ashok Nagar - Meerut South ₹150; PTI, 2025), at least ₹20 (NCRTC at launch, 2023).
# Premium coaches cost 1.2 times as much (NCRTC, June 2025).
NAMO_BHARAT_PER_KM, NAMO_BHARAT_MIN, PREMIUM_FACTOR = 2.7, 20, 1.2
NAMO_BHARAT_NOTE = "Namo Bharat fare estimated from published fares; standard to premium coach."


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


def metro_fare(distance_m: float, at: datetime) -> Fare:
    """One Delhi Metro journey, priced by its length; changing lines inside a station is
    part of the same journey. (The Metro charges the shortest distance between entry and
    exit, which the route ridden can exceed slightly.)"""
    table = METRO_SUNDAY if at.weekday() == 6 else METRO
    amount = _slab(table, distance_m)
    return Fare(min=amount, max=amount, note=METRO_NOTE)


def rapid_metro_fare() -> Fare:
    return Fare(min=RAPID_METRO[0], max=RAPID_METRO[1], note=RAPID_METRO_NOTE)


def namo_bharat_fare(distance_m: float) -> Fare:
    standard = max(NAMO_BHARAT_MIN, 5 * round(distance_m / 1000 * NAMO_BHARAT_PER_KM / 5))
    return Fare(min=standard, max=5 * round(standard * PREMIUM_FACTOR / 5), note=NAMO_BHARAT_NOTE)


def combine(parts: list[Fare]) -> Fare:
    """The fare for a journey of several tickets: their sums, with each note once."""
    notes = dict.fromkeys(part.note for part in parts if part.note)
    return Fare(
        min=sum(part.min for part in parts),
        max=sum(part.max for part in parts),
        note=" ".join(notes) or None,
    )
