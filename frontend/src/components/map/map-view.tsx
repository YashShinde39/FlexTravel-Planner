import Map, {
  AttributionControl,
  GeolocateControl,
  NavigationControl,
  type PaddingOptions,
} from 'react-map-gl/maplibre'
import { setWorkerUrl } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import type { ColorScheme } from '@/hooks/use-color-scheme'

// MapLibre decodes tiles in a web worker that it looks for next to its own file. Bundling
// renames that file, so the production build would fail to load the worker ("Worker failed
// to load"). Importing it with `?url` makes Vite ship the worker and gives its real URL.
setWorkerUrl(workerUrl)

// OpenFreeMap: free OpenStreetMap vector tiles, no API key (ADR-0013).
const MAP_STYLES: Record<ColorScheme, string> = {
  light: 'https://tiles.openfreemap.org/styles/positron',
  // "fiord" rather than "dark": the dark style references a texture it doesn't ship,
  // which renders as black blobs over airports and logs warnings.
  dark: 'https://tiles.openfreemap.org/styles/fiord',
}

const DELHI = { longitude: 77.209, latitude: 28.6139, zoom: 10.5 }

// Roughly Delhi NCR (west, south, east, north): keeps the camera where the planner has data.
const NCR_BOUNDS: [number, number, number, number] = [76.6, 28.15, 77.75, 29.0]

interface MapViewProps {
  colorScheme: ColorScheme
  isDesktop: boolean
  /** Screen space covered by the planner, so the map centres on what is still visible. */
  padding: PaddingOptions
}

export default function MapView({ colorScheme, isDesktop, padding }: MapViewProps) {
  return (
    <Map
      initialViewState={DELHI}
      maxBounds={NCR_BOUNDS}
      minZoom={9}
      mapStyle={MAP_STYLES[colorScheme]}
      padding={padding}
      attributionControl={false}
      style={{ position: 'absolute', inset: 0 }}
    >
      {/* On phones AppShell lifts the bottom-right controls above the sheet's edge. */}
      <AttributionControl compact position="bottom-right" />
      {isDesktop && <NavigationControl position="bottom-right" showCompass={false} />}
      <GeolocateControl position="bottom-right" positionOptions={{ enableHighAccuracy: true }} />
    </Map>
  )
}
