# ADR-0013: Frontend architecture: map-first, MapLibre + OpenFreeMap, shadcn/ui

- Status: Accepted (supersedes the map library and tile choice in ADR-0008; the map is
  Google Maps when a key is configured, ADR-0017)
- Date: 2026-10-23

## Context

The frontend was moved ahead of the GTFS import and RAPTOR so the product can be shown
early (roadmap change, October 2026). It must feel production-ready for the primary user:
a visitor to Delhi, most likely on a phone (ADR-0001).

ADR-0008 assumed Leaflet with OpenStreetMap's tile servers. OSM's tile usage policy
forbids heavy or production use of those servers, and raster tiles look dated next to
vector maps.

## Decision

- **Layout: map-first, one layout per kind of device, following Uber's web app.**
  (Amended 2026-10-24; first a full-screen map with a bottom sheet or a floating panel.)
  - *Laptops and tablets held sideways* (≥ 1024 × 500 px): a top bar, then the planner
    in columns with the map as an inset card beside them. From 1280 px the form, the
    route options and the map sit side by side; below that the form becomes a one-line
    "A → B" summary above the options.
  - *Phones and tablets held upright*: the map on top, the planner in a fixed panel
    below it. Before a search it is a short "Where to?" card; tapping a field opens a
    full-screen search with full-width suggestions. With routes, the map takes the top
    40% and the options the rest, with Directions pinned at the bottom.
  - *Phones held sideways* (landscape, ≥ 560 px): planner and map side by side, without
    the top bar. Uber stacks them here, which leaves a thin strip of map.
  - The panel on phones is fixed rather than draggable: simpler, and it let us drop
    `vaul`, whose sheet hid the rest of the page from screen readers.
- **Map: MapLibre GL + OpenFreeMap.** Open-source vector rendering; free OSM-based tiles
  with no API key. Styles: `liberty` (light; amended 2026-10-24 from the grey `positron`,
  for the familiar, colourful street-map look of Uber's and Rome2rio's maps) and `fiord`
  (dark). OpenFreeMap's `dark` style was rejected because it references a missing texture (black blobs over airports,
  console warnings).
- **Components: shadcn/ui on Radix**, with the Nova preset (Geist font, Lucide icons).
  The component source lives in the repo.
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

- **List-first layouts.** Simpler, but visitors lose spatial context. (Split layouts were
  first rejected too, for degrading into a long page on phones; the 2026-10-24 amendment
  uses a split per device instead, so each kind of screen gets its own arrangement.)
- **A draggable bottom sheet on phones** (vaul, or our own). Closer to Uber's app, but
  vaul's sheet trapped focus and hid the page from screen readers, and our own would be
  ~150 lines of touch handling to maintain.
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
