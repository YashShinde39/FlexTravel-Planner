import { type CSSProperties, lazy, Suspense, useState } from 'react'
import { Brand } from '@/components/brand'
import { PlannerPanel } from '@/components/planner/planner-panel'
import { useColorScheme } from '@/hooks/use-color-scheme'
import { useIsDesktop } from '@/hooks/use-media-query'
import { useTripPlanner } from '@/hooks/use-trip-planner'
import { useWindowHeight } from '@/hooks/use-window-height'
import { PlannerSheet } from './planner-sheet'
import { SHEET_PEEK_PX, SHEET_SNAP_POINTS, type SheetSnapPoint } from './sheet-snap-points'

// The map renderer is ~300 KB gzipped. Loading it lazily lets the planner render and accept
// typing straight away on slow mobile connections, while the map streams in behind it.
const MapView = lazy(() => import('@/components/map/map-view'))

const SIDE_PANEL_WIDTH = 400
const SIDE_PANEL_GAP = 16
// Keeps fitted routes clear of the floating brand pill at the top of phone screens.
const MOBILE_TOP_CLEARANCE = 56

/** Map-first layout (ADR-0013): full-screen map, planner as a side panel or bottom sheet. */
export function AppShell() {
  const colorScheme = useColorScheme()
  const isDesktop = useIsDesktop()
  const [snapPoint, setSnapPoint] = useState<SheetSnapPoint>(SHEET_SNAP_POINTS[0])
  const planner = useTripPlanner()
  const { plan, view } = planner.state

  // On phones, lower the sheet to half height when routes or directions appear, so the
  // route on the map is visible above it. Done while rendering, when the stage changes
  // (React's pattern for adjusting state to a change), rather than in an effect.
  const stage = `${plan.status}/${view}`
  const [seenStage, setSeenStage] = useState(stage)
  if (stage !== seenStage) {
    setSeenStage(stage)
    if (plan.status === 'ready' || view === 'details') setSnapPoint(SHEET_SNAP_POINTS[1])
  }

  // How much of the screen the sheet covers, so the map centres routes on what's left.
  // The fully open sheet is for typing; the map behind it then keeps the half-height framing.
  const windowHeight = useWindowHeight()
  const sheetHeight =
    snapPoint === SHEET_SNAP_POINTS[0] ? SHEET_PEEK_PX : Math.round(windowHeight * 0.55)

  const mapPadding = isDesktop
    ? { left: SIDE_PANEL_WIDTH + SIDE_PANEL_GAP * 2, top: 0, right: 0, bottom: 0 }
    : { left: 0, top: MOBILE_TOP_CLEARANCE, right: 0, bottom: sheetHeight }

  return (
    <main className="relative h-dvh w-full overflow-hidden bg-muted">
      {/* On phones, MapLibre's bottom-right controls sit just above the sheet. */}
      <div
        className="absolute inset-0 max-lg:[&_.maplibregl-ctrl-bottom-right]:mb-(--controls-offset)"
        style={{ '--controls-offset': `${sheetHeight}px` } as CSSProperties}
      >
        <Suspense fallback={<div className="absolute inset-0 animate-pulse bg-muted" aria-hidden />}>
          <MapView
            colorScheme={colorScheme}
            isDesktop={isDesktop}
            padding={mapPadding}
            origin={planner.state.origin}
            destination={planner.state.destination}
            option={planner.selected}
          />
        </Suspense>
      </div>

      {isDesktop ? (
        <aside
          aria-label="Trip planner"
          className="absolute top-4 bottom-4 left-4 z-10 overflow-y-auto rounded-2xl border bg-background/95 shadow-xl backdrop-blur supports-backdrop-filter:bg-background/85"
          style={{ width: SIDE_PANEL_WIDTH }}
        >
          <PlannerPanel planner={planner} />
        </aside>
      ) : (
        <>
          <Brand className="absolute top-[max(0.75rem,env(safe-area-inset-top))] left-3 z-10 rounded-full border bg-background/90 py-1 pr-3 pl-1 shadow-md backdrop-blur" />
          <PlannerSheet snapPoint={snapPoint} onSnapPointChange={setSnapPoint}>
            <PlannerPanel
              planner={planner}
              showBrand={false}
              onSearchFocus={() => setSnapPoint(SHEET_SNAP_POINTS[2])}
              inlineActions={false}
            />
          </PlannerSheet>
        </>
      )}
    </main>
  )
}
