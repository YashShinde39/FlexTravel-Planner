#!/usr/bin/env bash
# Prepare everything trip planning needs from the raw data (what `make data` runs):
#
#   1. Download OpenStreetMap extracts for northern and central India (Geofabrik), if
#      missing. NCR spans both: Delhi and Haryana are "northern", Noida, Ghaziabad and
#      Meerut (Uttar Pradesh) are "central".
#   2. Cut both down to Delhi NCR, merge them, and pull out stations and Metro lines
#      (osmium, in Docker).
#   3. Clean the bus feed and generate the Metro feed for the routing engine (ADR-0012,
#      ADR-0016).
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
OSM_ZONES="northern central"
OTP_DIR=data/work/otp
# Delhi NCR (west,south,east,north), up to Meerut for Namo Bharat; matches the map
# bounds in the frontend and the place search.
NCR_BBOX=76.6,28.15,77.8,29.12
OSMIUM_IMAGE=flextravel-osmium

command -v docker >/dev/null || fail "Docker not found. Install OrbStack (https://orbstack.dev)."
docker info >/dev/null 2>&1 || fail "Docker isn't running. Open OrbStack, then try again."
[ -f "$BUS_FEED" ] || fail "Bus feed missing: $BUS_FEED. See data/README.md for where to get it."

mkdir -p data/raw/osm data/work/osm data/work/metro "$OTP_DIR"

for zone in $OSM_ZONES; do
  url="https://download.geofabrik.de/asia/india/$zone-zone-latest.osm.pbf"
  raw="data/raw/osm/$zone-zone-latest.osm.pbf"
  [ -f "$raw" ] && continue
  step "Downloading OpenStreetMap extract for $zone India (~350 MB, first run only)"
  curl -fL --progress-bar -o "$raw.partial" "$url"
  expected=$(curl -fsSL "$url.md5" | cut -d' ' -f1)
  actual=$( (md5sum "$raw.partial" 2>/dev/null || md5 -r "$raw.partial") | cut -d' ' -f1)
  [ "$expected" = "$actual" ] || fail "Download corrupted (checksum mismatch). Run again."
  mv "$raw.partial" "$raw"
done

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
parts=()
for zone in $OSM_ZONES; do
  osmium extract --bbox "$NCR_BBOX" --strategy complete_ways --overwrite \
    -o "/data/work/osm/$zone-ncr.osm.pbf" "/data/raw/osm/$zone-zone-latest.osm.pbf"
  parts+=("/data/work/osm/$zone-ncr.osm.pbf")
done
# Objects on the state border are in both extracts; merge keeps one copy.
osmium merge --overwrite -o /data/work/otp/delhi-ncr.osm.pbf "${parts[@]}"

step "Extracting railway and metro stations"
osmium tags-filter --overwrite -o /data/work/stations.osm.pbf \
  /data/work/otp/delhi-ncr.osm.pbf n/railway=station
osmium export --overwrite --add-unique-id=type_id -f geojsonseq \
  -o /data/work/stations.geojsonseq /data/work/stations.osm.pbf

step "Extracting Metro and Namo Bharat lines"
osmium tags-filter --overwrite -o /data/work/metro/routes.osm.pbf \
  /data/work/otp/delhi-ncr.osm.pbf r/route=subway
osmium cat --overwrite -f opl -o /data/work/metro/routes.opl /data/work/metro/routes.osm.pbf
osmium tags-filter --overwrite -o /data/work/metro/entrances.osm.pbf \
  /data/work/otp/delhi-ncr.osm.pbf n/railway=subway_entrance,train_station_entrance
osmium cat --overwrite -f opl -o /data/work/metro/entrances.opl /data/work/metro/entrances.osm.pbf

step "Cleaning the bus feed"
(cd backend && uv run --quiet python -m app.data.bus_feed \
  "../$BUS_FEED" "../$OTP_DIR/dtc-bus.gtfs.zip")

step "Generating the Metro timetable"
(cd backend && uv run --quiet python -m app.data.metro_feed \
  ../data/work/metro/routes.opl "../$OTP_DIR/metro.gtfs.zip" \
  --entrances ../data/work/metro/entrances.opl)

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
