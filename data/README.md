# Data

Raw transit feeds are **not** stored in this repository (see
[ADR-0011](../docs/decisions/0011-data-sources-and-licensing.md)). Download them yourself
into `data/raw/`, which is gitignored.

## Delhi feeds

Source: Open Transit Data, Department of Transport, Government of NCT of Delhi.
Downloading means accepting the portal's [terms](https://otd.delhi.gov.in/terms).

| File to save as | Page | Button |
| --- | --- | --- |
| `data/raw/dtc-bus.zip` | https://otd.delhi.gov.in/data/static/ | "Download" (all static files as .zip) |
| `data/raw/dmrc-metro.zip` | https://otd.delhi.gov.in/data/staticDMRC/ | "Download" (all static files as .zip) |

The form asks for a usage type, a purpose and your name. For this project that is
**Non-Commercial**, with purpose **Academia** (or **Other**: personal portfolio project).

Note the date you downloaded each file. The inspection report records each file's size
and SHA-256, so changes between downloads are visible.

### Interim source (portal download broken)

As of 2026-10-23 the portal's file server is unreachable. Until it is fixed, use the
public mirror of the bus feed (official data, last refreshed February 2023):

```bash
mkdir -p data/raw
curl -L -o data/raw/dtc-bus-mirror-2023.zip \
  https://files.mobilitydatabase.org/mdb-3139/mdb-3139-202605111616/mdb-3139-202605111616.zip
shasum -a 256 data/raw/dtc-bus-mirror-2023.zip
# expect f5a8e196847c3c02da40578a05fcb764157e105f4f39ae628912673588ddcbe0
```

No metro mirror is available.

## Prepare for the planner

```bash
make data
```

This downloads the OpenStreetMap extracts for northern and central India from
[Geofabrik](https://download.geofabrik.de/asia/india.html) into `data/raw/osm/` (once,
about 575 MB, checksums verified; NCR spans both: Noida, Ghaziabad and Meerut are in
the central one). It then:

- cuts both to Delhi NCR and merges them;
- cleans the bus feed (ADR-0012);
- generates the Metro and Namo Bharat timetable from OpenStreetMap and
  `backend/app/data/metro_lines.py` (ADR-0016), printing a calibration report;
- loads stops and stations into Postgres;
- builds the OpenTripPlanner graph (ADR-0014).

Outputs go to `data/work/`. OpenStreetMap data is © OpenStreetMap contributors, ODbL.

The Metro report lists interchanges with no entrances mapped in OpenStreetMap; changing
lines there can't use its change time until someone maps them (at openstreetmap.org, as
`railway=subway_entrance` nodes).

## Inspect

```bash
uv run scripts/inspect_gtfs.py \
  --feed bus=data/raw/dtc-bus.zip --feed metro=data/raw/dmrc-metro.zip \
  --out docs/data/feed-inspection.md
```

Without uv: `pip install "pandas>=2.2,<3" "numpy>=2,<3"`, then run it with `python`.
