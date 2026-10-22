# ADR-0001: Product scope: transit routing for visitors in Delhi NCR

- Status: Accepted
- Date: 2026-10-23

## Context

The early prototype returned mock multi-day vacation itineraries ("Coastal Relaxation
Retreat, 6 days"), while the project plan described a multi-modal transit routing engine.
These are different products with different hard problems: itinerary curation and UX on one
side, timetable routing and data engineering on the other.

Routing quality depends entirely on transit data. India's open data is uneven. Delhi's
[Open Transit Data portal](https://otd.delhi.gov.in/documentation) publishes official GTFS
for DTC buses and Delhi Metro. An NCRTC (Namo Bharat) feed appears in public catalogues, but
no openly downloadable source was found (see ADR-0011). Bengaluru has an official bus feed
but only a community-built metro feed.
Chennai has a community feed. No current feeds were found for Mumbai, Hyderabad or Kochi.

## Decision

- **Product:** door-to-door journey planning across public transport and first/last-mile
  modes, presenting several options that trade off time, changes and cost.
- **Geography:** India only. Launch city: **Delhi NCR**, starting with DTC buses and Delhi
  Metro. NCRTC (Namo Bharat) is deferred until open data is available (ADR-0011).
- **Primary user:** a **visitor or newcomer** who does not know the network. They need
  landmark search, clear step-by-step directions and confidence at each change.
- **Language:** English only.

## Alternatives considered

- **Vacation/trip planner.** Rejected: less algorithmic depth, and none of the routing work
  would carry over.
- **Both, layered** (trip planner whose legs use the router). Possible later; doubles scope.
- **Bengaluru / Chennai.** Weaker metro data (community-maintained).
- **Several cities at once.** Every feed has its own quirks, and the cities don't connect
  to each other anyway. Depth on one city first; a second city later demonstrates that the
  design generalises.
- **Daily commuter as primary user.** Commuters already know their route; a planner adds
  the most value for people who don't.
- **Hindi or bilingual UI.** Deferred to keep scope focused.

## Consequences

- Multi-agency data (three feeds) must be merged, and stops must be linked for transfers.
- The visitor focus raises the priority of landmark search (ADR-0008) and of clear
  directions in the UI, above saved places or commute alerts.
- English-only text is not run through a translation layer. Adding Hindi later means
  extracting UI strings first.

## Why (in my words)

> _To fill in: why transit routing rather than trip planning? Why Delhi? Why visitors?_

## Questions an interviewer might ask

- Why not just use Google Maps? What does your planner do differently?
- What changes if you add Mumbai next?
- How did data availability shape your product decisions?
