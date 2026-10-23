#!/usr/bin/env bash
# Prepare everything trip planning needs from the raw data (what `make data` runs):
#
#   1. Download the OpenStreetMap extract for northern India (Geofabrik), if missing.
#   2. Cut it down to Delhi NCR and pull out railway and metro stations (osmium, in Docker).
#   3. Clean the bus feed for the routing engine (ADR-0012).
#   4. Load bus stops and stations into Postgres for the From/To suggestions.
#   5. Build the OpenTripPlanner graph (ADR-0014).
#
# Inputs live in data/raw/, outputs in data/work/; both are gitignored (ADR-0011).
# Re-running is safe. Takes about two minutes after the first download.

set -euo pipefail
cd "$(dirname "$0")/.."
unset VIRTUAL_ENV

red=$'\033[31m' dim=$'\033[2m' reset=$'\033[0m'
fail() { printf '%s✗ %s%s\n' "$red" "$1" "$reset" >&2; exit 1; }
step() { printf '%s→ %s%s\n' "$dim" "$1" "$reset"; }

BUS_FEED=data/raw/dtc-bus-mirror-2023.zip
OSM_URL=https://download.geofabrik.de/asia/india/northern-zone-latest.osm.pbf
OSM_RAW=data/raw/osm/northern-zone-latest.osm.pbf
OTP_DIR=data/work/otp
# Delhi NCR (west,south,east,north); matches the map bounds in the frontend.
NCR_BBOX=76.6,28.15,77.75,29.0
OSMIUM_IMAGE=flextravel-osmium

command -v docker >/dev/null || fail "Docker not found. Install OrbStack (https://orbstack.dev)."
docker info >/dev/null 2>&1 || fail "Docker isn't running. Open OrbStack, then try again."
[ -f "$BUS_FEED" ] || fail "Bus feed missing: $BUS_FEED. See data/README.md for where to get it."

mkdir -p "$(dirname "$OSM_RAW")" "$OTP_DIR"

if [ ! -f "$OSM_RAW" ]; then
  step "Downloading OpenStreetMap extract for northern India (~220 MB, first run only)"
  curl -fL --progress-bar -o "$OSM_RAW.partial" "$OSM_URL"
  expected=$(curl -fsSL "$OSM_URL.md5" | cut -d' ' -f1)
  actual=$( (md5sum "$OSM_RAW.partial" 2>/dev/null || md5 -r "$OSM_RAW.partial") | cut -d' ' -f1)
  [ "$expected" = "$actual" ] || fail "Download corrupted (checksum mismatch). Run again."
  mv "$OSM_RAW.partial" "$OSM_RAW"
fi

if ! docker image inspect "$OSMIUM_IMAGE" >/dev/null 2>&1; then
  step "Building a small osmium image (first run only)"
  docker build -q -t "$OSMIUM_IMAGE" - >/dev/null <<'EOF'
FROM debian:trixie-slim
RUN apt-get update && apt-get install -y --no-install-recommends osmium-tool \
    && rm -rf /var/lib/apt/lists/*
ENTRYPOINT ["osmium"]
EOF
fi
osmium() { docker run --rm -v "$PWD/data:/data" "$OSMIUM_IMAGE" "$@"; }

step "Cutting the map to Delhi NCR"
osmium extract --bbox "$NCR_BBOX" --strategy complete_ways --overwrite \
  -o /data/work/otp/delhi-ncr.osm.pbf /data/raw/osm/northern-zone-latest.osm.pbf

step "Extracting railway and metro stations"
osmium tags-filter --overwrite -o /data/work/stations.osm.pbf \
  /data/work/otp/delhi-ncr.osm.pbf n/railway=station
osmium export --overwrite --add-unique-id=type_id -f geojsonseq \
  -o /data/work/stations.geojsonseq /data/work/stations.osm.pbf

step "Cleaning the bus feed"
(cd backend && uv run --quiet python -m app.data.bus_feed \
  "../$BUS_FEED" "../$OTP_DIR/dtc-bus.gtfs.zip")

step "Loading bus stops and stations into the database"
docker compose up -d --wait db >/dev/null 2>&1 || fail "The database failed to start. See: docker compose logs db"
(cd backend && uv run --quiet alembic upgrade head &&
  uv run --quiet python -m app.data.import_places \
    "../$OTP_DIR/dtc-bus.gtfs.zip" ../data/work/stations.geojsonseq)

step "Building the OpenTripPlanner graph (about a minute)"
docker compose stop otp >/dev/null 2>&1 || true
docker compose run --rm -e JAVA_OPTS=-Xmx5g otp --build --save >data/work/otp/build.log 2>&1 ||
  fail "Graph build failed. See data/work/otp/build.log"
printf 'Done. Start the app with: make dev\n'
