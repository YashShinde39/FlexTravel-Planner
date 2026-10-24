# ADR-0017: Google Maps as the map, with the free map as fallback

- Status: Accepted (supersedes ADR-0013's map choice; the routing data is unchanged)
- Date: 2026-10-24

## Context

ADR-0013 chose MapLibre with free OpenFreeMap tiles, first the grey `positron` style and
then the colourful `liberty` style. Compared side by side with Uber and Rome2rio, the
owner found neither was the map they wanted. Both of those products show Google Maps:
light grey land, white roads, pale yellow highways, soft blue water, place icons
(hospitals, temples, malls), and labels in English and Hindi. No free OpenStreetMap
style reproduces that exactly.

## Decision

- **Google Maps** (Maps JavaScript API, through `@vis.gl/react-google-maps`) is the map
  whenever a key is configured in `frontend/.env.local`:
  `VITE_GOOGLE_MAPS_API_KEY` and `VITE_GOOGLE_MAPS_MAP_ID`. The key is a browser key
  restricted to this site's addresses and to the Maps JavaScript API; it is never
  committed (`*.local` is ignored).
- **Our routes are drawn on top**, as before: rides in the line's colour over a casing,
  walks as dots, stops passed as small ticks, and the start and end with name tags. The
  camera, the NCR bounds and dark mode (Google's dark scheme) work as on the free map.
- **Without a key, the free map is used** (MapLibre + OpenFreeMap, unchanged). Tests, CI
  and a fresh clone need no Google account, and the map still works if the key stops
  working.
- **Routing still runs on OpenStreetMap and the open transit feeds** (ADR-0011, 0014,
  0016). Only the picture underneath changes. Our data's credits stay in the planner.

## Alternatives considered

- **Restyling the free map to look like Google's.** No account and no cost, but about
  85% of the look and never exact.
- **MapTiler or Mapbox street styles.** Polished, but also not the map the owner
  pointed at, and also need a key.
- **Google Maps only, no fallback.** Simpler, but tests, CI and anyone cloning the repo
  would need a Google key.

## Consequences

- A Google Cloud project with a billing account is needed. Map loads are free up to
  Google's monthly quota for dynamic maps (about 10,000 a month), then charged per
  load. A budget alert in the Cloud console guards against surprises.
- Google's terms apply: its logo and credits must stay visible (on phones the map
  therefore stops above the planner panel's rounded edge), and its map is not to be
  combined with another provider's tiles.
- Two map implementations share the same props (`map-view.tsx`, `google-map-view.tsx`).
  Changes to how routes are drawn need making in both.
- The Google map is about 16 KB compressed plus Google's own script, against MapLibre's
  300 KB; with a key, MapLibre is never downloaded.

## Why (in my words)

> _To fill in: why Google's map rather than a free one styled to look like it? What do
> you give up by depending on Google here, and why is the fallback worth keeping?_

## Questions an interviewer might ask

- Your routes come from OpenStreetMap but you show Google's map. Is that a problem?
- How do you keep an API key that ships to the browser from being abused?
- What happens to the app if Google's map fails to load or the quota runs out?
- Why keep two map implementations?
