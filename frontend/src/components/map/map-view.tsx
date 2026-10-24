import { useEffect, useRef } from 'react'
import Map, {
  AttributionControl,
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
  // "liberty": a colourful street map (green parks, blue water, labelled roads), the
  // familiar look of the maps in Uber and Rome2rio.
  light: 'https://tiles.openfreemap.org/styles/liberty',
  // "fiord" rather than "dark": the dark style references a texture it doesn't ship,
  // which renders as black blobs over airports and logs warnings.
  dark: 'https://tiles.openfreemap.org/styles/fiord',
}

const DELHI = { longitude: 77.209, latitude: 28.6139, zoom: 10.5 }

// Roughly Delhi NCR (west, south, east, north): keeps the camera where the planner has data.
const NCR_BOUNDS: [number, number, number, number] = [76.6, 28.15, 77.8, 29.12]

// OpenStreetMap's attribution guidelines allow collapsing the map's credit after five
// seconds, as long as the (i) button still shows it. Left open, it covers much of a phone's map.
const ATTRIBUTION_COLLAPSE_MS = 5000

// Room around a fitted route, on top of the padding: up to 60px, less on a small map.
const FIT_MARGIN = 60
const FIT_MARGIN_SHARE = 0.12

export interface MapViewProps {
  colorScheme: ColorScheme
  /** Phones zoom by pinching; mice need buttons. */
  showZoomButtons: boolean
  /** Space over the map's edges taken by floating buttons, kept clear when framing routes. */
  padding: PaddingOptions
  /**
   * Changes when the map's box may have changed size (e.g. the options column appearing
   * beside it), so the route is framed again for the new size.
   */
  frameKey: string
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
  showZoomButtons,
  padding,
  frameKey,
  origin,
  destination,
  option,
}: MapViewProps) {
  const mapRef = useRef<MapRef>(null)
  const collapseTimer = useRef<number | undefined>(undefined)
  useEffect(() => () => window.clearTimeout(collapseTimer.current), [])

  function collapseAttributionLater() {
    collapseTimer.current = window.setTimeout(() => {
      mapRef.current
        ?.getContainer()
        .querySelector('.maplibregl-compact-show')
        ?.classList.remove('maplibregl-compact-show')
    }, ATTRIBUTION_COLLAPSE_MS)
  }

  // Move the camera when what's shown changes: fit the route, or frame the chosen places.
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const points: [number, number][] = option
      ? option.legs.flatMap((leg) => leg.geometry)
      : [origin, destination].filter((p) => p !== null).map((p) => [p.lon, p.lat])
    const bounds = boundsOf(points)
    if (!bounds) return
    // Read the box's current size now; MapLibre would otherwise notice a change a frame later.
    map.resize()
    if (points.length === 1) {
      map.flyTo({ center: points[0], zoom: Math.max(map.getZoom(), 13), duration: 800 })
    } else {
      const { clientWidth, clientHeight } = map.getContainer()
      const margin = Math.min(FIT_MARGIN, Math.round(Math.min(clientWidth, clientHeight) * FIT_MARGIN_SHARE))
      map.fitBounds(bounds, { padding: margin, maxZoom: 16, duration: 800 })
    }
    // Padding is listed by value: the object itself is new on every render.
  }, [option, origin, destination, padding.top, padding.bottom, padding.left, padding.right, frameKey])

  return (
    <Map
      ref={mapRef}
      initialViewState={DELHI}
      maxBounds={NCR_BOUNDS}
      minZoom={9}
      mapStyle={MAP_STYLES[colorScheme]}
      padding={padding}
      attributionControl={false}
      onLoad={collapseAttributionLater}
      style={{ position: 'absolute', inset: 0 }}
    >
      <TripLayers
        colorScheme={colorScheme}
        origin={origin}
        destination={destination}
        option={option}
      />
      <AttributionControl compact position="bottom-right" />
      {showZoomButtons && <NavigationControl position="bottom-right" showCompass={false} />}
    </Map>
  )
}
