/**
 * Google Maps settings (ADR-0017), from frontend/.env.local, which git ignores:
 *
 *   VITE_GOOGLE_MAPS_API_KEY=...   a browser key restricted to this site's addresses
 *   VITE_GOOGLE_MAPS_MAP_ID=...    a JavaScript map ID (markers and dark mode need one)
 *
 * Without a key the app uses the free OpenFreeMap map, so tests, CI and fresh clones
 * work without a Google account.
 */
export const GOOGLE_MAPS = {
  apiKey: import.meta.env.VITE_GOOGLE_MAPS_API_KEY ?? '',
  // Google's demo ID works for development but isn't meant for production.
  mapId: import.meta.env.VITE_GOOGLE_MAPS_MAP_ID || 'DEMO_MAP_ID',
}

export const USE_GOOGLE_MAPS = GOOGLE_MAPS.apiKey !== ''
