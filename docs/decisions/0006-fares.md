# ADR-0006: Fares from feed data, with official fare tables as fallback

- Status: Accepted
- Date: 2026-10-23

## Context

Fare is one of the three Pareto criteria (ADR-0003), so it must be reasonably accurate.
Delhi Metro charges by distance slabs; DTC buses have their own rules (e.g. AC vs non-AC);
autos use metered tariffs; app cabs have no public prices (ADR-0004). GTFS supports fares
(`fare_attributes.txt` / `fare_rules.txt`, or the newer Fares v2 files), but whether the
Delhi feeds include them is unknown until inspection.

## Decision

Use fare data from the feeds where present and correct. Where it is missing or wrong,
encode the **officially published fare tables** as versioned data files. Cab fares are
estimates and labelled as such.

## Alternatives considered

- **Defer fares.** A simpler first RAPTOR, but "cheapest" would be meaningless until later.
- **Rough per-km rates.** Quick, but misleading comparisons undermine the product.

## Consequences

- The data inspection (milestone M1) must report which fare files exist and whether they
  look plausible.
- Hand-encoded fare tables need a source citation and an "as of" date, and they will go
  stale.
- Fare must be computable per leg during McRAPTOR. Distance-based fares depend on where
  you board and alight, which affects label design.

## Why (in my words)

> _To fill in: why is fare accuracy worth the effort for this product?_

## Questions an interviewer might ask

- How do distance-slab fares interact with a label-based search?
- What do you do when the feed's fare data disagrees with the official website?
