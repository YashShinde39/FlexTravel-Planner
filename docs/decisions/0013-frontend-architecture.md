# ADR-0013: Frontend architecture: map-first, MapLibre + OpenFreeMap, shadcn/ui

- Status: Accepted (supersedes the map library and tile choice in ADR-0008)
- Date: 2026-10-23

## Context

The frontend was moved ahead of the GTFS import and RAPTOR so the product can be shown
early (roadmap change, October 2026). It must feel production-ready for the primary user:
a visitor to Delhi, most likely on a phone (ADR-0001).

ADR-0008 assumed Leaflet with OpenStreetMap's tile servers. OSM's tile usage policy
forbids heavy or production use of those servers, and raster tiles look dated next to
vector maps.

## Decision

- **Layout: map-first.** A full-screen map. On phones the planner is a non-dismissible
  bottom sheet with three heights (peek, half, full); on laptops (≥ 1024 px) it is a
  floating side panel. The map centres on the area the planner doesn't cover.
- **Map: MapLibre GL + OpenFreeMap.** Open-source vector rendering; free OSM-based tiles
  with no API key. Styles: `positron` (light) and `fiord` (dark). OpenFreeMap's `dark`
  style was rejected because it references a missing texture (black blobs over airports,
  console warnings).
- **Components: shadcn/ui on Radix**, with the Nova preset (Geist font, Lucide icons).
  The component source lives in the repo. The bottom sheet uses `vaul` directly, because
  shadcn's Drawer is a dismissible dialog with an overlay that would block the map.
- **Visual direction: clean + transit-line colours.** A neutral greyscale interface
  (near-black primary colour), so that colour is reserved for meaning: Metro line and
  bus route colours on the map and in directions.
- **Dark mode** follows the device setting, including the map style and MapLibre's
  controls.
- **Data before the backend exists: contract-first.** The API's request/response schemas
  are defined in FastAPI, with stub endpoints returning realistic journeys; TypeScript
  types are generated from the OpenAPI spec (next PR).
- **Testing:** Vitest + Testing Library for components and logic; Playwright end-to-end
  tests on desktop and phone viewports, failing on any console error.

## Alternatives considered

- **List-first or split layouts.** Simpler, but visitors lose spatial context, and split
  view degrades into a long scrolling page on phones.
- **MapTiler** (needs a key, has usage limits), **Leaflet + OSM tiles** (policy and dated
  look), **Google Maps** (billing, and conflicts with OSM-based data).
- **Mantine / MUI** (heavier; apps look like the library), **hand-built components**
  (accessibility becomes our job).
- **Bold branding** (competes with transit colours), **minimal utility** (undersells the
  project).
- **Mocking in the browser (MSW) or hardcoded data.** The API contract would live only in
  frontend code.

## Consequences

- OpenFreeMap is a small, donation-funded service with no uptime guarantee. The style
  URLs live in one place (`map-view.tsx`), so switching provider or self-hosting tiles is
  a one-line change.
- MapLibre is about 300 KB gzipped. It is lazy-loaded so the planner renders and accepts
  input before the map arrives. Its tile worker must be bundled explicitly (`?url` import
  plus `setWorkerUrl`), otherwise production builds fail to load it.
- Map attribution (OpenFreeMap, OpenMapTiles, OpenStreetMap) is always shown. Transit
  data attribution is in the planner panel (ADR-0011).
- Moving the frontend earlier means the API contract is designed before RAPTOR exists, and
  may need revising once routing realities are known.

## Why (in my words)

> _To fill in: why map-first for visitors? Why a neutral UI? Why build the frontend before the routing engine?_

## Questions an interviewer might ask

- Why MapLibre instead of Google Maps?
- How does the app behave on a slow mobile connection?
- How do you test a WebGL map?
- Your production build broke but dev worked. What happened, and how did you catch it?
