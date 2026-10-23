import { type CSSProperties, lazy, Suspense, useState } from 'react'
import { Brand } from '@/components/brand'
import { PlannerPanel } from '@/components/planner/planner-panel'
import { useColorScheme } from '@/hooks/use-color-scheme'
import { useHasSidePanel } from '@/hooks/use-media-query'
import { useTripPlanner } from '@/hooks/use-trip-planner'
import { useWindowHeight, useWindowWidth } from '@/hooks/use-window-size'
import { PlannerSheet } from './planner-sheet'
import { type SheetSnap, sheetHeightAt } from './sheet-snap-points'

// The map renderer is ~300 KB gzipped. Loading it lazily lets the planner render and accept
// typing straight away on slow mobile connections, while the map streams in behind it.
const MapView = lazy(() => import('@/components/map/map-view'))

/**
 * The side panel takes about 40% of a tablet or sideways phone, so the map keeps most of the
 * screen; 400px on laptops (as wide as the options need), a little more on big monitors.
 */
function sidePanelWidth(windowWidth: number): number {
  if (windowWidth >= 1920) return 440
  return Math.min(400, Math.max(320, Math.round(windowWidth * 0.42)))
}

/** Space between the side panel and the screen edges. */
function sidePanelGap(windowWidth: number): number {
  return windowWidth >= 1024 ? 16 : 12
}
// Keeps fitted routes clear of the floating brand pill at the top of phone screens.
const MOBILE_TOP_CLEARANCE = 56

/** Map-first layout (ADR-0013): full-screen map, planner as a side panel or bottom sheet. */
export function AppShell() {
  const colorScheme = useColorScheme()
  const hasSidePanel = useHasSidePanel()
  const [snap, setSnap] = useState<SheetSnap>('peek')
  const planner = useTripPlanner()
  const { plan, view } = planner.state

  // On phones, lower the sheet to half height when routes or directions appear, so the
  // route on the map is visible above it. Done while rendering, when the stage changes
  // (React's pattern for adjusting state to a change), rather than in an effect.
  const stage = `${plan.status}/${view}`
  const [seenStage, setSeenStage] = useState(stage)
  if (stage !== seenStage) {
    setSeenStage(stage)
    if (plan.status === 'ready' || view === 'details') setSnap('half')
  }

  // How much of the screen the sheet covers, so the map centres routes on what's left.
  // The fully open sheet is for typing; the map behind it then keeps the half-height framing.
  const windowWidth = useWindowWidth()
  const windowHeight = useWindowHeight()
  const sheetHeight = sheetHeightAt(snap === 'full' ? 'half' : snap, windowHeight)

  const panelWidth = sidePanelWidth(windowWidth)
  const panelGap = sidePanelGap(windowWidth)
  const mapPadding = hasSidePanel
    ? { left: panelWidth + panelGap * 2, top: 0, right: 0, bottom: 0 }
    : { left: 0, top: MOBILE_TOP_CLEARANCE, right: 0, bottom: sheetHeight }

  return (
    <main className="relative h-dvh w-full overflow-hidden bg-muted">
      {/* With the bottom sheet, MapLibre's bottom-right controls sit just above it. */}
      <div
        className={
          hasSidePanel
            ? 'absolute inset-0'
            : 'absolute inset-0 [&_.maplibregl-ctrl-bottom-right]:mb-(--controls-offset)'
        }
        style={{ '--controls-offset': `${sheetHeight}px` } as CSSProperties}
      >
        <Suspense fallback={<div className="absolute inset-0 animate-pulse bg-muted" aria-hidden />}>
          <MapView
            colorScheme={colorScheme}
            showZoomButtons={hasSidePanel}
            padding={mapPadding}
            origin={planner.state.origin}
            destination={planner.state.destination}
            option={planner.selected}
          />
        </Suspense>
      </div>

      {hasSidePanel ? (
        // As tall as its contents (a short card while searching), scrolling past the screen's
        // height. On a sideways phone, max() keeps it clear of the notch.
        <aside
          aria-label="Trip planner"
          className="absolute z-10 overflow-y-auto overscroll-contain rounded-2xl border bg-background/95 shadow-xl backdrop-blur supports-backdrop-filter:bg-background/85"
          style={{
            width: panelWidth,
            top: `max(${panelGap}px, env(safe-area-inset-top))`,
            left: `max(${panelGap}px, env(safe-area-inset-left))`,
            maxHeight: `calc(100dvh - ${panelGap * 2}px - env(safe-area-inset-top) - env(safe-area-inset-bottom))`,
          }}
        >
          <PlannerPanel planner={planner} />
        </aside>
      ) : (
        <>
          {/* The fully open sheet reaches the top of the screen, over where the brand floats. */}
          {snap !== 'full' && (
            <Brand className="absolute top-[max(0.75rem,env(safe-area-inset-top))] left-3 z-10 rounded-full border bg-background/90 py-1 pr-3 pl-1 shadow-md backdrop-blur" />
          )}
          <PlannerSheet snap={snap} onSnapChange={setSnap}>
            <PlannerPanel
              planner={planner}
              showBrand={false}
              onSearchFocus={() => setSnap('full')}
              inlineActions={false}
            />
          </PlannerSheet>
        </>
      )}
    </main>
  )
}
