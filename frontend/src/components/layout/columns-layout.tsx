import { Brand } from '@/components/brand'
import { PlannerMap } from '@/components/map/planner-map'
import { Attribution } from '@/components/planner/attribution'
import { DirectionsBar } from '@/components/planner/directions-bar'
import { RouteOptions } from '@/components/planner/route-options'
import { SearchCard } from '@/components/planner/search-card'
import { TripDirections } from '@/components/planner/trip-directions'
import { TripSummary } from '@/components/planner/trip-summary'
import { useMediaQuery, WIDE_QUERY } from '@/hooks/use-media-query'
import type { TripPlanner } from '@/hooks/use-trip-planner'
import { cn } from '@/lib/utils'

/** The options, or one option's directions, in a column that scrolls under a pinned button. */
function ResultsColumn({
  planner,
  showSummary,
  className,
}: {
  planner: TripPlanner
  showSummary: boolean
  className?: string
}) {
  const details = planner.state.view === 'details'
  return (
    <div className={cn('flex min-h-0 flex-col', className)}>
      <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
        <div className="flex flex-col gap-4 px-1 pb-4">
          {details ? (
            <TripDirections planner={planner} />
          ) : (
            <>
              <h2 className="font-heading text-3xl font-bold tracking-tight">Choose a route</h2>
              {showSummary && <TripSummary planner={planner} />}
              <RouteOptions planner={planner} />
            </>
          )}
          <Attribution className="pt-2" />
        </div>
      </div>
      {!details && <DirectionsBar planner={planner} className="px-1" />}
    </div>
  )
}

/**
 * Laptops (`desktop`) and phones held sideways (`sideways`): the planner in columns beside
 * the map. As on Uber's site, a desktop has a top bar and shows the map as a card; from
 * 1280px the form stays beside the options, and below that it becomes a one-line summary.
 */
export function ColumnsLayout({
  planner,
  variant,
}: {
  planner: TripPlanner
  variant: 'desktop' | 'sideways'
}) {
  const desktop = variant === 'desktop'
  const wide = useMediaQuery(WIDE_QUERY) && desktop
  const { view } = planner.state
  const showForm = view === 'search' || wide
  const showResults = view !== 'search'

  return (
    <div className="flex h-dvh flex-col bg-background">
      {desktop && (
        <header className="flex h-16 shrink-0 items-center border-b px-6 xl:px-10">
          <Brand />
        </header>
      )}
      <main
        className={cn(
          'flex min-h-0 flex-1',
          desktop
            ? 'gap-6 p-6 xl:px-10'
            : 'gap-2 p-2 pl-[max(0.5rem,env(safe-area-inset-left))] pr-[max(0.5rem,env(safe-area-inset-right))]',
        )}
      >
        <aside
          aria-label="Trip planner"
          className={cn(
            'flex min-h-0 shrink-0 gap-6',
            !desktop && 'w-[clamp(300px,46vw,400px)] flex-col gap-3 pt-2 pl-2',
          )}
        >
          {!desktop && <Brand />}
          {showForm &&
            (desktop ? (
              <div className={cn('flex shrink-0 flex-col gap-4', wide ? 'w-80' : 'w-[360px]')}>
                <div className="rounded-2xl border-2 p-5">
                  <SearchCard planner={planner} />
                </div>
                {!showResults && <Attribution />}
              </div>
            ) : (
              <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain pr-1 pb-2">
                <SearchCard planner={planner} />
                <Attribution className="mt-4" />
              </div>
            ))}
          {showResults && (
            <ResultsColumn
              planner={planner}
              showSummary={!wide}
              className={desktop ? 'w-[420px]' : 'flex-1 pr-1'}
            />
          )}
        </aside>
        <div
          className={cn(
            'relative min-w-0 flex-1 overflow-hidden bg-muted',
            desktop ? 'rounded-2xl' : 'rounded-xl',
          )}
        >
          <PlannerMap
            planner={planner}
            showZoomButtons={desktop}
            frameKey={`${variant}/${showForm}/${showResults}`}
          />
        </div>
      </main>
    </div>
  )
}
