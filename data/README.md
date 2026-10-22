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

Note the date you downloaded each file. The inspection report records file sizes so
changes between downloads are visible.

## Inspect

```bash
uv run scripts/inspect_gtfs.py \
  --feed bus=data/raw/dtc-bus.zip --feed metro=data/raw/dmrc-metro.zip \
  --out docs/data/feed-inspection.md
```

Without uv: `pip install "pandas>=2.2,<3" "numpy>=2,<3"`, then run it with `python`.
