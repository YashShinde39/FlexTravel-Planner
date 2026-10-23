# ADR-0004: Walk, auto-rickshaw and app cabs for first and last mile

- Status: Accepted
- Date: 2026-10-23

## Context

Few trips start and end at a stop. In Indian cities the gap is commonly covered on foot, by
auto-rickshaw, or by app-based cabs and bike taxis (Ola, Uber, Rapido). Bicycles are less
common for this. These modes have no timetable, so they are not part of RAPTOR's scheduled
network.

## Decision

Support **walking**, **auto-rickshaw** and **app cabs/bike taxis** as access/egress and
short direct modes. Bicycles are excluded.

- **Auto fares:** government-notified meter tariffs for Delhi (base fare + per-km),
  encoded as data so they can be updated.
- **App cab fares:** clearly labelled *estimates*. There is no public pricing API, and
  surge pricing makes exact prices impossible.

## Alternatives considered

- **Walking only.** Smallest scope, but unrealistic for Indian cities.
- **Bicycle.** Uncommon for first/last mile in Delhi; would clutter results.

## Consequences

- Auto/cab legs have a waiting/pickup overhead and a cost, and feed the fare criterion
  (ADR-0003).
- Road distances are needed for fares. The first version may use straight-line distance
  times a detour factor; road routing (e.g. OSRM on OpenStreetMap) is a later upgrade.
- The UI must distinguish estimated from regulated fares.

## Why (in my words)

> _To fill in: why do these modes matter for a visitor in Delhi?_

## Questions an interviewer might ask

- How do you estimate a cab fare without an API? How wrong can it be?
- How do non-scheduled modes fit into a timetable algorithm like RAPTOR?
