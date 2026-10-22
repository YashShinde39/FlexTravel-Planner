# ADR-0011: Data sources and licensing

- Status: Accepted
- Date: 2026-10-23

## Context

Sources investigated for Delhi transit data (as of October 2026):

| Source | Content | Access | Terms |
| --- | --- | --- | --- |
| [Delhi Open Transit Data (OTD)](https://otd.delhi.gov.in/documentation) | DTC buses (3,464 stops, 543 routes, updated June 2024); Delhi Metro (updated August 2023) | Download form: usage type, purpose, name, acceptance of terms | [Terms](https://otd.delhi.gov.in/terms): reproduction allowed if accurate and with source prominently credited (cl. 22), but "modification … will be a violation" (cl. 7) |
| [Delhi Transport Stack](https://chartr.in/products/transport-stack/) | Reportedly open GTFS for DTC + DIMTS buses with fares, plus open GTFS-Realtime | No public download link or licence found | Unknown |
| [Mobility Database](https://mobilitydatabase.org/feeds/gtfs/mdb-3139) / Transitland archive | Mirror of the DTC bus feed, timetable covering 2022–2024 | Direct download | Licence not stated |
| NCRTC (Namo Bharat) | Listed by an aggregator (2 routes, 7 stops) | Only on request under a data contract | Unknown |

The OTD portal also states that bus `stop_times` are estimates assuming constant speed
(ADR-0007).

## Decision

1. **Primary source:** the official OTD portal feeds (DTC buses, Delhi Metro). The project
   owner downloads them through the portal's form (non-commercial, academic/portfolio use).
2. **Pursue Delhi Transport Stack** in parallel by contacting the Transport Department or
   Chartr. If granted, it would add DIMTS buses, fares and real-time data.
3. **NCRTC is deferred** until an openly available feed exists.
4. **Raw data stays out of git.** Feeds live in a gitignored `data/raw/` directory and are
   obtained by whoever runs the project, including the deployed server. The repository
   contains code, derived statistics (e.g. the inspection report) and attribution, never
   the feed files.
5. **Attribution:** the app and README prominently credit "Open Transit Data, Department
   of Transport, Government of NCT of Delhi".

## Alternatives considered

- **Mirrors as the main source.** No form, but outdated and with an unclear licence.
- **Commit raw feeds.** Easier reproducibility, but arguably redistributes modified
  contents against clause 7.
- **Hand-build an NCRTC feed** from the published timetable. Feasible (a single line), but
  adds maintenance; can be reconsidered later.
- **Request the aggregator's NCRTC feed.** Unknown licence; may require a commercial
  contract.

## Consequences

- No CI job can download the official feeds automatically. Tests use small synthetic
  fixtures or a fixture derived under clear terms.
- Deployment needs a step that provides the feed files to the server (e.g. uploaded to
  private storage), designed in M3.
- The terms are ambiguous about transforming data into an app. This is noted as a known
  risk, and clarification can be requested from the Transport Department together with the
  Transport Stack enquiry.
- The bus data is from June 2024 and the metro data from August 2023. The inspection
  report must check calendar validity, as calendars may have expired.

## Why (in my words)

> _To fill in: why the official source over easier mirrors? Why keep data out of git?_

## Questions an interviewer might ask

- How do you keep your data current?
- How do you test a pipeline whose input you can't commit?
- What would change if you got the Transport Stack feed?
