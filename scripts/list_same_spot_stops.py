# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas>=2.2,<3"]
# ///
"""List groups of stops that share exact coordinates but have different names.

Each group gets OpenStreetMap and Google Maps links so it can be checked by eye
(ADR-0012, decision 3). Output stays local: it contains feed data, which is not committed
(ADR-0011).

    uv run scripts/list_same_spot_stops.py data/raw/dtc-bus-mirror-2023.zip \
        --sample 20 > data/work/same-spot-stops.md
"""

import argparse
import zipfile

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("feed", help="GTFS zip")
    parser.add_argument("--sample", type=int, help="random sample of N groups (default: all)")
    parser.add_argument("--seed", type=int, default=7, help="sample seed, for repeatability")
    args = parser.parse_args()

    with zipfile.ZipFile(args.feed) as archive, archive.open("stops.txt") as handle:
        stops = pd.read_csv(handle, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    stops["lat"] = pd.to_numeric(stops["stop_lat"])
    stops["lon"] = pd.to_numeric(stops["stop_lon"])

    groups = [g for _, g in stops.groupby(["lat", "lon"]) if g["stop_name"].nunique() > 1]
    if args.sample and args.sample < len(groups):
        picks = pd.Series(range(len(groups))).sample(args.sample, random_state=args.seed)
        groups = [groups[i] for i in sorted(picks)]

    print(f"# Same-spot stops ({len(groups)} groups)\n")
    print("For each group: is it one physical stop with two names, two stops on opposite "
          "sides of the road given the same point, or bad coordinates?\n")
    print("| # | Stops (id: name) | Map | Your verdict |")
    print("|---|---|---|---|")
    for i, group in enumerate(groups, 1):
        lat, lon = group["lat"].iloc[0], group["lon"].iloc[0]
        names = "<br>".join(f"{r.stop_id}: {r.stop_name}" for r in group.itertuples())
        links = (f"[OSM](https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=19/{lat}/{lon}) · "
                 f"[Google](https://www.google.com/maps/search/?api=1&query={lat},{lon})")
        print(f"| {i} | {names} | {links} | |")


if __name__ == "__main__":
    main()
