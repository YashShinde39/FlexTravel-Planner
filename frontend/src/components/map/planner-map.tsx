import { lazy, Suspense } from 'react'
import type { PaddingOptions } from 'react-map-gl/maplibre'
import { useColorScheme } from '@/hooks/use-color-scheme'
import type { TripPlanner } from '@/hooks/use-trip-planner'
import { USE_GOOGLE_MAPS } from './google-maps-config'

// Google Maps when a key is configured (ADR-0017), otherwise the free OpenFreeMap map.
// Either is loaded lazily, so the planner renders and accepts typing straight away on slow
// mobile connections while the map streams in behind it.
const MapView = lazy(() => (USE_GOOGLE_MAPS ? import('./google-map-view') : import('./map-view')))

const NO_PADDING: PaddingOptions = { top: 0, right: 0, bottom: 0, left: 0 }

interface PlannerMapProps {
  planner: TripPlanner
  showZoomButtons?: boolean
  padding?: PaddingOptions
  /** See MapView. */
  frameKey: string
}

/** The map for the planner's trip: its places, and the selected option's route. */
export function PlannerMap({
  planner,
  showZoomButtons = false,
  padding = NO_PADDING,
  frameKey,
}: PlannerMapProps) {
  const colorScheme = useColorScheme()
  return (
    <Suspense fallback={<div className="absolute inset-0 animate-pulse bg-muted" aria-hidden />}>
      <MapView
        colorScheme={colorScheme}
        showZoomButtons={showZoomButtons}
        padding={padding}
        frameKey={frameKey}
        origin={planner.state.origin}
        destination={planner.state.destination}
        option={planner.selected}
      />
    </Suspense>
  )
}
