# ADR-0015: Product direction: beat Rome2rio on Delhi NCR, in depth

- Status: Accepted (extends ADR-0001's scope; amends ADR-0011 on Namo Bharat)
- Date: 2026-10-24

## Context

The owner's goal is a planner that beats Rome2rio, with more useful features and more
accurate, reliable routes. Rome2rio was reviewed on 2026-10-24. Its laptop site sits
behind a bot check, so this is based on its phone site and on published reviews.

What Rome2rio does well:

- It covers 240+ countries and every way of travelling: flights, trains, buses, ferries
  and driving.
- Its timetables come from GTFS feeds from 20,000+ operators.
- Each option has one total time and a price range, with BEST, CHEAPEST and FASTEST
  labels and links to book.
- For Delhi it has the Metro. For Kashmere Gate → India Gate it offered "Subway + bus,
  29 min, ₹34–53" and "Subway, 35 min".

Where it is weak, for Delhi:

- **Times can be unrealistic.** It gives a taxi from Kashmere Gate to India Gate as 10
  minutes. The trip is about 8.5 km through Old Delhi; we estimate 28. Published
  reviews report India driving times and distances far off, and routes or buses that
  don't exist.
- **No departure times**, only durations.
- **No autos, e-rickshaws or bike taxis.** These are how Delhi covers the last mile.
- **Nothing says how far to trust a result.** It doesn't say whether a time is
  scheduled, estimated or live, or how old the data is.
- **Clutter.** An "app is easier" pop-up covers the results, and hotel, car and tour
  ads fill the rest of the page.

FlexTravel was already ahead on realistic auto and cab times, meter fares, real bus
departures and step-by-step directions. It was behind on one thing: the Metro.

## Decision

**Where to compete:** Delhi NCR, in depth. Every local mode, with times we can stand
behind. Rome2rio's breadth is not the target; trips to other cities and all of India are
out of scope for now.

**Accuracy and reliability, in this order:**

1. **Metro routing.** The official feed is still unreachable (ADR-0011), so we
   generate a Delhi Metro timetable ourselves:
   - lines and stations from OpenStreetMap;
   - frequencies and first/last trains from DMRC's published information;
   - the result written as a GTFS feed whose times are marked as estimated.

   When the official feed becomes available it replaces ours. Same format, no code
   change. The generator gets its own ADR when it is built.
2. **Trust labels on every time.** Each time says whether it is scheduled, estimated or
   live, and how old its data is. Users can report a wrong route.
3. **Live bus positions** from DTC's GTFS-Realtime feed on Delhi's Open Transit Data
   portal, once that server is reachable and we have an API key.

**Travel options to add:**

- Metro + auto or e-rickshaw combinations for the last mile.
- Bike taxis and app cabs (Rapido, Uber, Ola), shown as price ranges from published rate
  cards. None has a public API, so these are labelled estimates.
- Namo Bharat (the Delhi–Meerut RRTS line) and Indian Railways suburban trains in NCR.
  This brings forward what ADR-0011 deferred.
- Accurate bus fares: AC and non-AC, and free travel for women on DTC and cluster buses.
  Who qualifies is to be checked against current Delhi rules when this is built.

**Features beyond routing:**

- **Saved places and trips, and sharing, on the device with no login.** Home, work and
  recent trips are kept in the browser. A shared link carries the trip itself. No
  accounts, no personal data on our server.
- **Safety and accessibility.** Late-night and women's-safety notes, the Metro's women's
  coach, step-free stations and lifts.

**Not chosen for now:** better road times from a paid traffic API, Hindi, offline use,
and intercity trips.

**Order of work:** the Metro first, then the rest. Metro + auto combos, Namo Bharat and
step-free station information all build on it.

**Principles that come from the review:**

- No pop-ups over results.
- No ads.
- Never a single confident number where the truth is a range or an estimate.

## Alternatives considered

- **Delhi plus trips out of Delhi** (Agra, Jaipur…). This is Rome2rio's home ground, and
  Indian Railways has no open timetable feed, so it would need scraping or a paid API.
- **All of India.** The widest reach, but it ends up as a thin layer of estimates like
  Rome2rio's. Open transit data exists for only a few cities.
- **Waiting for the official Metro feed.** The most accurate, but there is no date for
  it.
- **The 2018 Metro feed on Codeberg.** A real DMRC timetable, but eight years old and
  missing newer lines and stations.
- **User accounts for saved trips.** These would sync across devices, but they need
  authentication, a users table and a privacy policy.
- **Live buses first.** This is blocked on the data portal being reachable.
- **Quick wins first** (labels, fares, cab prices). These are visible sooner, but they
  leave the biggest gap open.

## Consequences

- Metro times are estimates until the official feed arrives, and the trust labels make
  that visible. Generating the timetable is real data engineering. It also gives RAPTOR
  (ADR-0003) a second agency to route across.
- Several features rely on published information that changes: Metro frequencies, bike
  taxi and app cab rate cards, fare rules. Each needs a source and an "as of" date in the
  code, as the fares already have.
- Live buses depend on an outside service we don't control. The planner must work
  without them and fall back to scheduled times.
- With no accounts, saved trips stay on one device and are lost if the browser's data is
  cleared. Shared links must hold only the trip, never anything personal.
- Rome2rio stays the benchmark. Comparing the same Delhi trips against it, and against
  OTP, is part of judging the accuracy work.

## Why (in my words)

> _To fill in: why compete on depth in one region rather than breadth? Why build our own
> Metro timetable instead of waiting? Why keep saved trips on the device?_

## Questions an interviewer might ask

- Rome2rio covers the world. Why would anyone use a Delhi-only planner?
- How do you know your times are more accurate than Rome2rio's? How would you measure
  it?
- How do you make a timetable for a network whose official timetable you can't get?
  How wrong can it be?
- How do you show users how much to trust a time?
- How do saved trips work without accounts? What happens to privacy when someone shares
  a link?
