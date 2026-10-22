# ADR-0003: RAPTOR, extended to McRAPTOR on time, changes and fare

- Status: Accepted
- Date: 2026-10-23

## Context

Public transport routing is time-dependent: an edge is only usable when a vehicle departs.
Graph algorithms like Dijkstra and A* can be adapted to this with a time-expanded or
time-dependent graph, but they optimise one number, and on city-scale timetables they
explore many redundant states.

**RAPTOR** (Round-bAsed Public Transit Optimized Router; Delling, Pajor and Werneck,
Microsoft Research, 2012) works on the timetable directly. In round *k* it scans each
route once and finds the earliest arrival at every stop using at most *k* vehicles.
Results come out "Pareto-optimal in arrival time and number of changes" without any
priority queue. **McRAPTOR** generalises this by keeping a *bag* of non-dominated labels
per stop, so further criteria can be added.

The product promises to compare trade-offs (ADR-0001). Six candidate criteria were
identified: arrival time, changes, fare, walking, auto/cab spend, and reliability. Pareto
sets grow very quickly with each criterion, which slows the search and floods users with
near-identical options.

## Decision

- Implement **RAPTOR** first (arrival time + changes), then extend it to **McRAPTOR**.
- **Pareto criteria:** arrival time, number of changes, fare (fare includes auto/cab cost).
- **Not Pareto criteria:**
  - Walking: a user-set limit, plus a tie-breaker.
  - Auto/cab spend: a toggle, and shown as a separate line in each result.
  - Reliability: a score used to rank and label options (see ADR-0007).
- First- and last-mile legs (walk, auto, cab) are computed separately and fed into
  RAPTOR's first and last rounds, as in standard multi-modal RAPTOR variants.
- The algorithm is **implemented by the project owner** (guided build: explainer,
  skeleton, failing tests; see ADR-0010).

## Alternatives considered

- **Keep the earlier McA\* graph search.** Works on small networks, but it was written by
  the assistant rather than owned, and it is slower on real timetables.
- **All six criteria as Pareto criteria.** Full optimality, but the search slows sharply
  and users see too many options.
- **One weighted score.** Fast, but hides the trade-offs the product exists to show.
- **OpenTripPlanner / r5 as a black box.** Production quality, but removes the core
  engineering contribution.
- **Connection Scan Algorithm (CSA).** Also excellent for earliest arrival; RAPTOR's
  round structure maps more naturally to "number of changes" and multi-criteria bags.

## Consequences

- Data must be shaped into RAPTOR's structures: routes as ordered stop sequences, trips
  sorted by departure, and a footpath (transfer) list per stop. This drives the import
  pipeline design.
- Trips on the same GTFS route with different stop sequences must be split into separate
  RAPTOR routes.
- Performance on Delhi-scale data is unknown until measured (milestone M2). Python may be
  too slow; NumPy arrays, a process pool, or a compiled core are later options.

## Why (in my words)

> _To fill in: explain RAPTOR's rounds in two sentences. Why limit Pareto criteria to three?_

## Questions an interviewer might ask

- Walk me through one RAPTOR round. What is "marking" and why does it help?
- Why does RAPTOR not need a priority queue?
- What is a Pareto set, and why does it explode as you add criteria?
- How would you support "arrive by 9:00" instead of "depart at 8:00"?
- Where is the time spent, and how would you make it faster?
