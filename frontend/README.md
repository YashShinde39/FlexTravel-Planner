# Frontend

React 19 + TypeScript + Vite, styled with Tailwind CSS and shadcn/ui (Radix), with a
MapLibre GL map on OpenFreeMap tiles. Design decisions: [ADR-0013](../docs/decisions/0013-frontend-architecture.md).

## Commands

```bash
npm install
npm run dev         # http://localhost:5173, proxies /api to the backend on :8000
npm run build       # typecheck + production build into dist/
npm run lint        # oxlint
npm test            # unit tests (Vitest + Testing Library)
npm run e2e         # Playwright, desktop and phone viewports (builds and serves dist/)
```

First-time Playwright setup: `npx playwright install chromium`.

## Layout

```
src/
  App.tsx                         entry component
  components/
    layout/app-shell.tsx          picks the layout for the device (ADR-0013)
    layout/columns-layout.tsx     laptops and sideways phones: planner columns beside the map
    layout/stacked-layout.tsx     phones and upright tablets: map on top, panel below
    map/planner-map.tsx           lazy-loads the map for the planner's trip
    map/map-view.tsx              free map (MapLibre): styles, NCR bounds, framing the route
    map/google-map-view.tsx       Google Maps, used when a key is set (ADR-0017)
    map/trip-layers.tsx           the selected route: ride lines, walking dots, stops, markers
    planner/                      the pieces layouts arrange: search card, phone search
                                  screen, From/To combobox, route options, directions
    trip/option-list.tsx          route options, ride-app style
    trip/trip-details.tsx         step-by-step timeline for one option
    brand.tsx                     logo + name
    ui/                           shadcn/ui components (generated, then owned)
  hooks/use-trip-planner.ts       planner state (reducer) and automatic planning
  hooks/use-place-search.ts       debounced, cancellable place search
  lib/api/                        API client; schema.d.ts is generated (make api-types)
  test/                           test setup, jsdom stubs, recorded API fixtures
e2e/                              Playwright specs
```

## Notes

- **API types are generated** from the backend's OpenAPI schema: run `make api-types`
  from the repository root after changing the API, and commit both files in `src/lib/api/`.
- **Tests don't need the backend.** Unit and browser tests answer API calls from recorded
  responses in `src/test/fixtures/`.
- **Look:** monochrome, ride-app inspired (Uber). Black is the only accent; green marks
  "Fastest"/"Cheapest". The route is drawn in the text colour with a background-coloured
  casing, so it reads on both light and dark maps.
- **Dark mode** follows the device. `index.html` sets the `dark` class before first paint
  to avoid a white flash; `useColorScheme` keeps it in sync.
- **The map is lazy-loaded** (about 300 KB gzipped) so the planner is usable first on slow
  connections.
- **MapLibre's tile worker** is imported with `?url` and registered with `setWorkerUrl`.
  Without that, production builds fail with "Worker failed to load" while dev still works.
  The e2e test fails on console errors to catch this.
- **Components in `src/components/ui`** come from shadcn/ui and are edited like our own
  code. Add more with `npx shadcn@latest add <name>`.
