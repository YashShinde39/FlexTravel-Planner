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
    layout/app-shell.tsx          map-first layout: side panel (≥1024 px) or bottom sheet
    layout/planner-sheet.tsx      always-present mobile sheet (vaul), three snap heights
    map/map-view.tsx              MapLibre map, lazy-loaded; styles and NCR bounds
    planner/planner-panel.tsx     planner contents shared by sheet and side panel
    brand.tsx                     logo + name
    ui/                           shadcn/ui components (generated, then owned)
  hooks/                          media queries, light/dark scheme
  test/                           test setup and jsdom stubs
e2e/                              Playwright specs
```

## Notes

- **Dark mode** follows the device. `index.html` sets the `dark` class before first paint
  to avoid a white flash; `useColorScheme` keeps it in sync.
- **The map is lazy-loaded** (about 300 KB gzipped) so the planner is usable first on slow
  connections.
- **MapLibre's tile worker** is imported with `?url` and registered with `setWorkerUrl`.
  Without that, production builds fail with "Worker failed to load" while dev still works.
  The e2e test fails on console errors to catch this.
- **Components in `src/components/ui`** come from shadcn/ui and are edited like our own
  code. Add more with `npx shadcn@latest add <name>`.
