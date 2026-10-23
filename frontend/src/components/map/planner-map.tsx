import { lazy, Suspense } from 'react'
import type { PaddingOptions } from 'react-map-gl/maplibre'
import { useColorScheme } from '@/hooks/use-color-scheme'
import type { TripPlanner } from '@/hooks/use-trip-planner'

// The map renderer is ~300 KB gzipped. Loading it lazily lets the planner render and accept
// typing straight away on slow mobile connections, while the map streams in behind it.
const MapView = lazy(() => import('./map-view'))

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
