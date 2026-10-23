# Roadmap

Milestones are delivered as small PRs (ADR-0010). There is no fixed deadline; each
milestone ships something that works before the next one starts.

**Change (October 2026):** the frontend was moved ahead of the import and RAPTOR
(ADR-0013). It is built against a contract-first stub API: A shell → B API contract →
C trip search → D results. Data and routing work continue afterwards in the original order.

**Change (October 2026, later):** instead of a stub, trip planning runs on
OpenTripPlanner as an interim engine (ADR-0014), with real Delhi bus data, stop and
station search, and auto/cab estimates. RAPTOR replaces OTP behind the same interface in
M2; OTP then serves as the reference to check RAPTOR's results against.

**Change (October 2026, after reviewing Rome2rio):** the product competes with Rome2rio
on Delhi NCR in depth (ADR-0015). The work below comes next, in this order. RAPTOR (M2)
is unchanged and can start whenever the owner chooses; the Metro feed gives it a second
agency to route across.

- **R1. Metro.** Generate a Delhi Metro GTFS feed from OpenStreetMap lines and stations
  plus DMRC's published frequencies and first/last trains, marked as estimated. Add it
  to `make data`, then to the results. Replace it with the official feed when available.
- **R2. Metro + auto or e-rickshaw combinations** for the last mile.
- **R3. Trust labels:** scheduled, estimated or live, and how old the data is. A way to
  report a wrong route.
- **R4. Accurate bus fares:** AC and non-AC, and free travel for women on DTC and cluster
  buses.
- **R5. Bike taxis and app cabs:** Rapido, Uber and Ola price ranges from published rate
  cards.
- **R6. Namo Bharat and NCR suburban trains.**
- **R7. Saved places, recent trips and shareable links,** stored on the device.
- **R8. Safety and accessibility:** late-night and women's-safety notes, the women's
  coach, step-free stations and lifts.
- **R9. Live bus positions** from DTC's GTFS-Realtime feed, once Delhi's Open Transit
  Data server is reachable and we have an API key.

## M1: Delhi data

1. **Feed inspection.** Download the DTC bus and Delhi Metro feeds (ADR-0011) and write a
   report on what's actually in them: sizes, service calendars, fare files, coordinate
   quality, times past midnight, stops that should be shared between agencies. The
   decisions that depend on this are fare handling (ADR-0006), bus buffers (ADR-0007) and
   memory budget (ADR-0009).
2. **Backend skeleton.** FastAPI, Docker Compose with Postgres + PostGIS, Alembic, CI.
3. **Import.** Load stops, routes, trips, stop times and calendars for both agencies.
4. **Transfers** *(owner-built)*. Link stops across agencies with walking footpaths.
5. **Estimated-time flags** and transfer buffers for buses.

## M2: RAPTOR *(guided build)*

6. RAPTOR explainer with a worked example on a toy network.
7. Data structures for RAPTOR (routes, trips, footpaths) built from the database.
8. Skeleton and failing tests; the owner implements the rounds.
9. Run on all of Delhi: measure, profile, optimise.

## M3: First usable product

10. Frontend skeleton (Vite + TypeScript + Tailwind + Leaflet map).
11. Plan endpoint and stop search API.
12. Results UI with step-by-step directions.
13. Deploy (ADR-0009).

## M4: Trade-offs

14. McRAPTOR with fares (feed data + official tables).
15. Auto-rickshaw and app cab access legs.
16. Reliability score and labels.

## M5: Visitor features

17. OpenStreetMap landmark import and search.
18. Map pin origin/destination; Nominatim address search.
