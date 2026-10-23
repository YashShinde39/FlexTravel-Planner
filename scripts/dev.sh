#!/usr/bin/env bash
# Start FlexTravel for local development.
#
#   scripts/dev.sh        database + API + web app, one terminal (what `make dev` runs)
#   scripts/dev.sh api    database + API only
#   scripts/dev.sh web    web app only (expects the API to be running separately)
#
# Ctrl+C stops the servers. The database keeps running; `make db-down` stops it.
# Ports default to 8000 (API) and 5173 (web); override with API_PORT / WEB_PORT.
# Written for the bash 3.2 that ships with macOS.

set -euo pipefail
cd "$(dirname "$0")/.."

# uv manages backend/.venv itself. A different virtualenv left activated in the shell (e.g.
# by an editor) only makes uv print a confusing "VIRTUAL_ENV does not match" warning.
unset VIRTUAL_ENV

mode="${1:-all}"
api_port="${API_PORT:-8000}"
web_port="${WEB_PORT:-5173}"
export API_PORT="$api_port" # read by frontend/vite.config.ts to proxy /api
case "$mode" in all | api | web) ;; *) echo "usage: $0 [all|api|web]" >&2; exit 2 ;; esac

red=$'\033[31m' dim=$'\033[2m' cyan=$'\033[36m' magenta=$'\033[35m' reset=$'\033[0m'
fail() { printf '%s✗ %s%s\n' "$red" "$1" "$reset" >&2; exit 1; }
step() { printf '%s→ %s%s\n' "$dim" "$1" "$reset"; }

# --- Preflight: explain common setup problems instead of failing with a stack trace.
needs_api=false needs_web=false
[ "$mode" != web ] && needs_api=true
[ "$mode" != api ] && needs_web=true

if $needs_api; then
  command -v docker >/dev/null || fail "Docker not found. Install OrbStack (https://orbstack.dev)."
  docker info >/dev/null 2>&1 || fail "Docker isn't running. Open OrbStack, then try again."
  command -v uv >/dev/null || fail "uv not found. Install it: https://docs.astral.sh/uv/"
fi
if $needs_web; then
  command -v npm >/dev/null || fail "Node.js not found. Install Node 20.19 or newer: https://nodejs.org"
fi

port_in_use() { command -v lsof >/dev/null && lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1; }
$needs_api && port_in_use "$api_port" &&
  fail "Port $api_port is busy, probably an API server still running elsewhere. Stop it (Ctrl+C in its terminal), find it with: lsof -iTCP:$api_port -sTCP:LISTEN, or use another port: API_PORT=8001 make dev"
$needs_web && port_in_use "$web_port" &&
  fail "Port $web_port is busy, probably a web dev server still running elsewhere. Stop it, find it with: lsof -iTCP:$web_port -sTCP:LISTEN, or use another port: WEB_PORT=5174 make dev"

# --- Prepare
if $needs_api; then
  step "Starting database"
  docker compose up -d --wait db >/dev/null 2>&1 || fail "The database container failed to start. See: docker compose logs db"
  step "Applying migrations"
  (cd backend && uv run --quiet alembic upgrade head)
fi
if $needs_web && [ ! -d frontend/node_modules ]; then
  step "Installing frontend dependencies (first run only)"
  (cd frontend && npm ci --no-fund --no-audit)
fi

# --- Run. Each server gets its own process group (set -m), so cleanup can stop a server
# together with everything it spawned (uvicorn's reloader, Vite's workers).
set -m
pids=()
cleanup() {
  trap - INT TERM EXIT
  for pid in "${pids[@]}"; do kill -- "-$pid" 2>/dev/null || true; done
  wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

# Prefix every log line with a coloured label so the two servers' output is easy to tell apart.
label() { awk -v tag="$1" '{ print tag " " $0; fflush() }'; }

if $needs_api; then
  (cd backend && uv run uvicorn app.main:app --reload --host 127.0.0.1 --port "$api_port" 2>&1 |
    label "${cyan}api${reset}") &
  pids+=($!)
fi
if $needs_web; then
  (cd frontend && npm run dev -- --host 127.0.0.1 --port "$web_port" --strictPort 2>&1 |
    label "${magenta}web${reset}") &
  pids+=($!)
fi

$needs_web && printf '\n  App   http://127.0.0.1:%s\n' "$web_port"
$needs_api && printf '  API   http://127.0.0.1:%s/docs\n' "$api_port"
printf '  Press Ctrl+C to stop.\n\n'
wait
