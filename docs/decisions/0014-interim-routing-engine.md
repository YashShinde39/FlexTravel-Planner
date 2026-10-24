# ADR-0014: OpenTripPlanner as the interim routing engine, behind our own interface

- Status: Accepted (bus buffer amended by ADR-0016)
- Date: 2026-10-23

## Context

The owner wanted a working planner (suggestions, route options, directions on the map)
before writing RAPTOR (ADR-0003). That is several weeks of guided work away. A
placeholder was needed that gives real journeys on real Delhi data now, without becoming
something the app depends on in ways RAPTOR can't replace.

Options considered for the placeholder: a stub API with made-up journeys, a minimal
"direct buses only" planner, porting the prototype's McA* engine, or an established
open-source engine. The owner chose an established engine.

Two serious candidates:

- **OpenTripPlanner 2** (v2.10, Java). Used by transit agencies worldwide. Its transit
  search *is* RAPTOR internally, and it routes walking and car legs on OpenStreetMap
  streets.
- **MOTIS 2** (v2.11, C++). Lighter and fast, with built-in address autocomplete, but
  less widely known and less documented.

Separately, ADR-0008 planned on Nominatim for address search. Nominatim's usage policy
forbids search-as-you-type, which is exactly what the From/To fields need.

## Decision

- **OpenTripPlanner 2.10** runs as a Docker service next to Postgres. `make data` builds
  its graph from the cleaned bus feed (ADR-0012) and an OpenStreetMap extract of Delhi NCR;
  `make dev` serves it.
- The API never exposes OTP. Trip planning goes through a small `TripPlanner` interface
  (`backend/app/trips/engine.py`) with two methods: public-transport journeys and
  street routes. OTP is one implementation (`otp.py`); RAPTOR will be another.
- Everything product-specific stays in our code, above the interface: fares (ADR-0006),
  auto and cab estimates (ADR-0004), grouping repeat departures, keeping only journeys
  that are a real trade-off (Pareto on arrival, changes, walking, fare), and labels.
- Transfer buffer for estimated bus times (ADR-0007): **5 minutes**, as OTP's
  `transferSlack`. A first guess, to be tuned.
- **Auto and cab times** use typical Delhi speeds by time of day (18 km/h at peak,
  25 km/h by day, 35 km/h at night) instead of OTP's empty-road times, plus a wait for
  the vehicle. Marked as estimates.
- **Address and landmark search** uses **Photon** (an OpenStreetMap geocoder built for
  autocomplete), proxied and cached by the API. Stops and stations come from our own
  database first. This amends ADR-0008's choice of Nominatim.

## Alternatives considered

- **Stub journeys.** Fast to build, but the options would be made up.
- **Direct buses only.** Honest and small, but most real trips need a change.
- **Port the prototype engine.** Full routes now, but it undercuts "I built the router".
- **MOTIS 2.** Lighter to host, but a smaller community and fewer docs.
- **Call OTP from the browser.** No backend work, but the engine would leak into the
  frontend and RAPTOR could no longer replace it invisibly.

## Consequences

- One more service to run: about 1.6 GB of memory, ready about 5 seconds after start.
  The graph builds in under a minute. Hosting (ADR-0009) needs a plan for it.
- RAPTOR now has a reference implementation on the same data: its results and speed can
  be compared with OTP's directly.
- Photon's public instance is a fair-use service. The API caches results, and
  suggestions fall back to stops and stations only if Photon is down.
- Metro is still missing: there is no metro feed to load (ADR-0011). Adding one is a
  `make data` change, with no code change.

## Why (in my words)

> _To fill in: why put a pre-built engine in now, and why behind an interface rather than
> calling it directly? What will you compare when your RAPTOR replaces it?_

## Questions an interviewer might ask

- OTP already uses RAPTOR. Why write your own?
- How do you know your RAPTOR gives correct results? (Compare it with OTP on the same
  queries.)
- What did you have to add on top of the engine to make the options useful?
- Why does the browser never talk to the engine directly?
