# ADR-0012: Bus feed cleaning and route display rules

- Status: Accepted (one item pending, see 3)
- Date: 2026-10-23

## Context

The feed inspection ([findings](../data/findings.md)) of the DTC/DIMTS bus feed
(interim mirror, February 2023; ADR-0011) found problems the import must handle:

- One `service_id`, valid 2022-01-01 to 2024-01-01: expired, and with no weekday/weekend
  variation.
- 20,428 stop visits where the same stop appears on two consecutive rows. Investigation
  showed these are **not** loops or turnarounds:
  - both rows always have identical times;
  - the stop sequence numbers are always adjacent;
  - there are 0 cases where the stop before equals the stop after.
  
  Separately, **2,293 trips genuinely revisit a stop** after other stops (real loops and
  branches).
- 127 locations where stops with different names share identical coordinates.
- Route names pack number, variant code and direction together (`764STLDOWN`). Two news
  guides ([Amar Ujala](https://www.amarujala.com/photo-gallery/automobiles/delhi-commuters-guide-to-dtc-bus-codes-and-route-letters-2026-02-07),
  [India.com](https://www.india.com/hindi-news/gk/dtc-bus-route-codes-meaning-ltd-stl-ext-tms-oms-a-b-c-delhi-transport-guide-8276911/))
  define some codes. Checked against stop counts in the feed:

  | Code | Claimed meaning | Evidence in feed |
  | --- | --- | --- |
  | STL | Short turn loop (partial route) | Confirmed: shorter than base in 301/381 pairs, median 27 vs 44 stops |
  | A/B/C | Branch of the main route | Consistent: mostly slightly shorter |
  | EXT | Extension beyond last stop | **Contradicted**: shorter than base in 35/61 pairs |
  | LTD | Limited stop | Inconclusive (3 pairs) |
  | TMS/OMS | Inner/Outer Ring Road; (+) clockwise | Not testable from stop counts |
  | LNK/LINK, CL, E, L, (NS), SPL | Not defined by any source | — |

## Decision

1. **Calendar:** ignore dates and treat every trip as running every day. The UI states
   that the bus timetable dates from 2023 and times are approximate. Proper calendar
   handling arrives with fresh data that has real calendars.
2. **Repeated stops:** collapse *consecutive* duplicate stop visits into one (first
   arrival, last departure) and log the count. **Non-consecutive revisits (loops) are
   kept.** RAPTOR must therefore identify stops by their position within a route, not
   only by stop ID.
3. **Same-spot stops with different names:** *pending.* The owner will inspect a sample
   on a map and decide between merging, or keeping them separate with a zero-length
   transfer. Recorded here when decided.
4. **Route display:** show the route code **as printed on the bus** (e.g. "764 STL",
   towards the final stop), because that is what a visitor must match at the stop. Add
   explanations only for codes verified against data (STL, A/B/C). Unknown or contradicted
   codes are shown without explanation.

## Alternatives considered

- **Calendar:** shift it to a rolling window (fiction presented as data), or respect dates
  strictly (no buses run, so the planner is useless).
- **Repeated stops:** keep them as published (visitors see "Mitraon Village" twice), or
  drop affected trips (loses about 21% of trips).
- **Route display:** number only (a visitor can't tell 764 STL from 764 EXT), or explain
  every code from the articles (EXT's published meaning contradicts the data).

## Consequences

- The importer needs a cleaning step with counts in its output, so cleaning is visible
  and testable.
- RAPTOR test cases must include a route that visits the same stop twice.
- Route-code explanations live in a small, reviewed lookup table, extendable as
  meanings are confirmed (e.g. from a DTC source or the Transport Department).

## Why (in my words)

> _To fill in: why collapse duplicates but keep loops? Why show codes you don't fully understand?_

## Questions an interviewer might ask

- How did you tell a data artifact apart from a real loop?
- You found a published definition that contradicted your data. What did you do?
- Why does a repeated stop break naive RAPTOR implementations?
