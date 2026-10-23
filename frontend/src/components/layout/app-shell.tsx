import { type CSSProperties, lazy, Suspense, useState } from 'react'
import { Brand } from '@/components/brand'
import { PlannerPanel } from '@/components/planner/planner-panel'
import { useColorScheme } from '@/hooks/use-color-scheme'
import { useIsDesktop } from '@/hooks/use-media-query'
import { PlannerSheet } from './planner-sheet'
import { SHEET_PEEK_PX, SHEET_SNAP_POINTS, type SheetSnapPoint } from './sheet-snap-points'

// The map renderer is ~300 KB gzipped. Loading it lazily lets the planner render and accept
// typing straight away on slow mobile connections, while the map streams in behind it.
const MapView = lazy(() => import('@/components/map/map-view'))

const SIDE_PANEL_WIDTH = 400
const SIDE_PANEL_GAP = 16

/** Map-first layout (ADR-0013): full-screen map, planner as a side panel or bottom sheet. */
export function AppShell() {
  const colorScheme = useColorScheme()
  const isDesktop = useIsDesktop()
  const [snapPoint, setSnapPoint] = useState<SheetSnapPoint>(SHEET_SNAP_POINTS[0])

  const mapPadding = isDesktop
    ? { left: SIDE_PANEL_WIDTH + SIDE_PANEL_GAP * 2, top: 0, right: 0, bottom: 0 }
    : { left: 0, top: 0, right: 0, bottom: SHEET_PEEK_PX }

  return (
    <main className="relative h-dvh w-full overflow-hidden bg-muted">
      {/* On phones, MapLibre's bottom-right controls sit just above the peeking sheet. */}
      <div
        className="absolute inset-0 max-lg:[&_.maplibregl-ctrl-bottom-right]:mb-(--controls-offset)"
        style={{ '--controls-offset': `${SHEET_PEEK_PX}px` } as CSSProperties}
      >
        <Suspense fallback={<div className="absolute inset-0 animate-pulse bg-muted" aria-hidden />}>
          <MapView colorScheme={colorScheme} isDesktop={isDesktop} padding={mapPadding} />
        </Suspense>
      </div>

      {isDesktop ? (
        <aside
          aria-label="Trip planner"
          className="absolute top-4 bottom-4 left-4 z-10 overflow-y-auto rounded-2xl border bg-background/95 shadow-xl backdrop-blur supports-backdrop-filter:bg-background/85"
          style={{ width: SIDE_PANEL_WIDTH }}
        >
          <PlannerPanel />
        </aside>
      ) : (
        <>
          <Brand className="absolute top-[max(0.75rem,env(safe-area-inset-top))] left-3 z-10 rounded-full border bg-background/90 py-1 pr-3 pl-1 shadow-md backdrop-blur" />
          <PlannerSheet snapPoint={snapPoint} onSnapPointChange={setSnapPoint}>
            <PlannerPanel
              showBrand={false}
              onSearchFocus={() => setSnapPoint(SHEET_SNAP_POINTS[2])}
            />
          </PlannerSheet>
        </>
      )}
    </main>
  )
}
