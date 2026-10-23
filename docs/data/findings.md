# Feed inspection: findings and open questions

Interpretation of [feed-inspection.md](feed-inspection.md), the generated statistics.

## Provenance

The official OTD download was unavailable on 2026-10-23: the portal page loads, but its
file server (`traffickarma.iiitd.edu.in:9010`) refuses connections. As an **interim
source** (ADR-0011), the bus feed was taken from a public mirror:

- Mobility Database `mdb-3139`, originally committed to Transitland's archive on 2023-02-25
  as "latest Delhi feed downloaded manually" from `opendata.iiitd.edu.in` (the portal's
  predecessor). This is the same official data, about three years old.
- SHA-256 `f5a8e196…ddcbe0`, saved locally as `data/raw/dtc-bus-mirror-2023.zip`.
- **No metro feed** could be obtained. Metro inspection is pending.

## Findings

### 1. Bus times really are constant-speed estimates (ADR-0007 confirmed)
Hop speeds are 15.0 km/h at the 5th, 50th and 95th percentiles. 98.9% of trips have a
per-trip speed variation (CV) below 0.05. Every bus is modelled as moving at exactly
15 km/h, so the times say nothing about real traffic. The transfer buffer is necessary,
and "approximate" labels are honest.

### 2. The service calendar has expired
There is one `service_id`, running every day from 2022-01-01 to 2024-01-01. Read strictly,
no bus runs today. There are no `calendar_dates` exceptions, so there is no
weekday/weekend difference either.

### 3. No fare data
There are no fare files at all, so fares come from official tables (ADR-0006). The feed
has a `zone_id` on stops, but with 4,556 distinct values it looks like a per-stop ID, not
a fare zone.

### 4. Two agencies in one feed
1,964 DIMTS routes (cluster buses) and 1,000 DTC routes, 78,515 trips in total. The
current official portal lists 543 routes, so the present-day official feed may cover
less, or be structured differently.

### 5. Route names encode number, variant and direction
`route_short_name` is empty for every route. `route_long_name` packs everything together:
`764STLDOWN`, `511ALNKSTLUP`, `764EXTDOWN`. 2,919 of 2,964 end in `UP` or `DOWN`. Visitors
need "Bus 764 towards X", so names must be parsed. The meaning of the middle codes
(`STL`, `EXT`, `LNK`, `A`) is not documented in the feed.

### 6. Duplicate stops
- 0.9% of hops have zero travel time. Of these, 98.5% join stops with identical
  coordinates, and **68% are literally the same stop listed twice in a row** within a trip.
- 419 coordinate points hold more than one stop; at 127 of them the stops have different
  names.
- 4,636 stops share a name with another stop. That is expected: a stop on each side of
  the road.

### 7. Night service and times past midnight
1,167 trips start before 05:00, and times run up to 30:20 (06:20 the next morning, in
GTFS notation). RAPTOR must handle times ≥ 24:00 and trips from the previous service day.

### 8. RAPTOR shape and memory (ADR-0003, ADR-0009)
Each route has exactly one stop pattern (2,964 patterns), so routes map one-to-one to
RAPTOR routes. 3.3 M stop events ≈ 39 MB as compact arrays, versus ≈ 650 MB as Python
objects. **Compact arrays are required** to fit a free hosting tier.

## Decisions

Recorded in [ADR-0012](../decisions/0012-bus-feed-cleaning-and-display.md):

1. **Expired calendar:** ignore dates and run every trip daily; label the timetable as 2023.
2. **Repeated consecutive stops:** collapse them. Investigation ruled out loops (identical
   times, adjacent sequence numbers, no turnaround pattern). The 2,293 trips with genuine
   revisits are kept.
3. **Same-spot stops:** one place with several names → merge under the feed name that
   matches Google Maps (reference only), else the OSM name. Different places on one point
   → coordinates corrected from OSM via owner-reviewed proposals, or flagged.
4. **Route codes:** shown as printed on the bus, explained only where verified against the
   data (STL and A/B/C confirmed; EXT contradicted).
5. **Bus transfer buffer:** decided in the transfer-linking stage.
