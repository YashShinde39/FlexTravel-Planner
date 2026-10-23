import { useEffect, useRef } from 'react'
import Map, {
  AttributionControl,
  GeolocateControl,
  type MapRef,
  NavigationControl,
  type PaddingOptions,
} from 'react-map-gl/maplibre'
import { LngLatBounds, setWorkerUrl } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import type { ColorScheme } from '@/hooks/use-color-scheme'
import type { Place, TripOption } from '@/lib/api/client'
import { TripLayers } from './trip-layers'

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

// Room around a fitted route, on top of the space the planner covers.
const FIT_MARGIN = 60

interface MapViewProps {
  colorScheme: ColorScheme
  isDesktop: boolean
  /** Screen space covered by the planner, so the map centres on what is still visible. */
  padding: PaddingOptions
  origin: Place | null
  destination: Place | null
  option: TripOption | null
}

/** Everything the camera should show: the selected route, or else the chosen places. */
function boundsOf(points: [number, number][]): LngLatBounds | null {
  if (points.length === 0) return null
  return points.reduce(
    (bounds, point) => bounds.extend(point),
    new LngLatBounds(points[0], points[0]),
  )
}

export default function MapView({
  colorScheme,
  isDesktop,
  padding,
  origin,
  destination,
  option,
}: MapViewProps) {
  const mapRef = useRef<MapRef>(null)

  // Move the camera when what's shown changes: fit the route, or frame the chosen places.
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const points: [number, number][] = option
      ? option.legs.flatMap((leg) => leg.geometry)
      : [origin, destination].filter((p) => p !== null).map((p) => [p.lon, p.lat])
    const bounds = boundsOf(points)
    if (!bounds) return
    if (points.length === 1) {
      map.flyTo({ center: points[0], zoom: Math.max(map.getZoom(), 13), duration: 800 })
    } else {
      map.fitBounds(bounds, { padding: FIT_MARGIN, maxZoom: 16, duration: 800 })
    }
    // Padding is listed by value: the object itself is new on every render.
  }, [option, origin, destination, padding.top, padding.bottom, padding.left, padding.right])

  return (
    <Map
      ref={mapRef}
      initialViewState={DELHI}
      maxBounds={NCR_BOUNDS}
      minZoom={9}
      mapStyle={MAP_STYLES[colorScheme]}
      padding={padding}
      attributionControl={false}
      style={{ position: 'absolute', inset: 0 }}
    >
      <TripLayers
        colorScheme={colorScheme}
        origin={origin}
        destination={destination}
        option={option}
      />
      {/* On phones AppShell lifts the bottom-right controls above the sheet's edge. */}
      <AttributionControl compact position="bottom-right" />
      {isDesktop && <NavigationControl position="bottom-right" showCompass={false} />}
      <GeolocateControl position="bottom-right" positionOptions={{ enableHighAccuracy: true }} />
    </Map>
  )
}
