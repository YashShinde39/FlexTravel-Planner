# ADR-0016: A generated Metro timetable, from OpenStreetMap and published frequencies

- Status: Accepted (amends ADR-0014's bus buffer and ADR-0011's map extract)
- Date: 2026-10-24

## Context

ADR-0015 put the Metro first. The official Delhi Metro feed still can't be downloaded
(ADR-0011), and the 2018 feed on Codeberg turned out to be a sample (Yellow Line only, a
flat 2 minutes between stations). The Metro publishes no timetable in any machine-readable
form: only scattered figures for frequencies, first and last trains, and fares.

OpenStreetMap, on the other hand, maps every line as a route relation with its stops in
order and the track between them, in both directions, including Rapid Metro Gurgaon and
Namo Bharat. It also maps many station entrances.

Building it also showed that our map was missing Noida, Greater Noida, Ghaziabad and
Meerut: they are in Uttar Pradesh, which Geofabrik puts in its "central zone" extract,
not the "northern zone" we downloaded.

## Decision

Generate a GTFS feed (`backend/app/data/metro_feed.py`, values in `metro_lines.py`) as
part of `make data`, and load it into OpenTripPlanner next to the bus feed.

- **Lines:** the Delhi Metro's Red, Yellow, Blue, Green, Violet, Pink, Magenta and Grey
  lines, plus Rapid Metro Gurgaon and Namo Bharat (pulled forward from roadmap R6). The
  Airport Express and Noida's Aqua Line are left out for now.
- **Stations and track** from OpenStreetMap. Distances between stations are measured
  along each line's own track (a shortest path over its ways), not as straight lines.
- **Time between stations** = 40 s at each stop + distance at a running speed. The
  speed is calibrated per line so that published end-to-end times come out right: the
  Red Line (63 min, so 45 km/h between stops) for the Delhi Metro and Rapid Metro, and
  Namo Bharat's own 55 min (101 km/h).
- **Frequencies** from a per-line table: weekday peaks, the rest of the day, late
  evening and Sundays, plus first and last trains. Each value has its source and date
  where one exists; the rest are marked as estimates. Written as GTFS frequencies with
  exact times, so the engine sees real departures.
- **Changing lines** takes a per-station time (4 minutes by default; longer at known long
  walks such as Hauz Khas, 8, and Kashmere Gate, 7). Interchanges are modelled inside:
  their entrances mapped in OpenStreetMap and a platform per line, joined by walkways
  (GTFS pathways) that take half the change time each, plus the walk from a far entrance.
- **Every Metro time is marked as an estimate**, as bus times are, until an official feed
  replaces this one. That needs no code change, only a new feed id.
- **Fares:** Delhi Metro distance slabs (from 25 August 2025, cheaper on Sundays), one
  ticket for a whole journey across lines; Rapid Metro and Namo Bharat priced separately.
- **Map extract:** both Geofabrik zones are downloaded, cut to NCR and merged. The NCR box
  grows north to 29.12° to reach Modipuram (Meerut).
- **Bus buffer (amends ADR-0014):** the 5 minutes now apply only around buses: 2.5
  minutes when boarding a bus and 2.5 when getting off. A bus-to-bus change keeps its 5
  minutes, and Metro changes are only the station's change time.

## What building it taught us

These shaped the design; each was found by running real queries.

- **OpenTripPlanner 2.10 ignores GTFS minimum transfer times.** It loads them
  (station-wide or platform-to-platform), but the routing never applies them: Hauz Khas
  changes came out at 1 minute against a rule of 8. Pathways are what it honours.
- **Its own walk between platforms follows the streets outside**, so it misses skywalks:
  Sikanderpur's Rapid Metro platform is 140 m from the Yellow Line's, but the walk came
  out at 1,255 m, and the Rapid Metro was never used.
- **Entrances have to be the mapped ones.** Entrances guessed at the station's middle or
  at the platforms often landed on walkways inside the station that don't reach the
  street, cutting whole stations off. Mapped entrances sit on footways and attach.
- **Frequency-based trips need exact times.** With `exact_times=0` OpenTripPlanner let
  trips board at any moment, and changes between lines broke.

## Alternatives considered

- **Fixed time between stations** (e.g. 2 minutes each). Simplest, but wrong for long
  gaps such as the Yamuna crossings.
- **Scraping the Metro's journey planner.** Official station-to-station times, but it may
  break their terms of use and breaks whenever their site changes.
- **One frequency pattern for every line.** Wrong for the Grey Line and Rapid Metro.
- **One change time everywhere, or the engine's own walk.** Too optimistic for deep
  interchanges and too pessimistic for same-platform ones; the engine's walk also misses
  skywalks.

## Consequences

- Times are estimates. Two published end-to-end times disagree with each other: with
  the Red Line calibration, the Yellow Line comes out at 87 minutes against a published
  69. One of the two sources (both third-party) is wrong. This is the first number to
  check against the Metro's own journey planner, and a calibration report prints it on
  every `make data`.
- 7 of the 29 interchanges (Ashok Park Main, Dwarka, Karkarduma, Majlis Park, New Ashok
  Nagar, Welcome, Yamuna Bank) have no entrances in OpenStreetMap, so their change times
  fall back to the engine's walk. Mapping their entrances in OpenStreetMap fixes them:
  a contribution back to the open data the project uses. `make data` lists them.
- Entering a modelled interchange takes half its change time (2 minutes at most); other
  stations are entered directly, as the engine links them to the street itself.
- Values in `metro_lines.py` and `fares.py` go stale: each carries its source and an
  "as of" date to re-check.
- The first download is larger (about 575 MB for both zones), once.
- RAPTOR (ADR-0003) now has a second agency and real interchanges to route across.

## Why (in my words)
To test the working of the website for having metro data later. 
> _To fill in: why generate a timetable rather than wait? Why calibrate speeds on
> published times? Why model interchanges with walkways instead of transfer rules?_

## Questions an interviewer might ask

- How do you build a timetable for a network that doesn't publish one? How wrong can
  it be, and how would you find out?
- Your sources disagree on the Yellow Line's journey time. How do you decide which is
  right?
- Why didn't GTFS minimum transfer times work, and how did you find out?
- Why are times between stations "overhead plus distance at a speed" rather than a
  speed alone?
- How would you replace this with the official feed when it arrives?
