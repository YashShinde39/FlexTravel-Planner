import { ArrowLeft, Info } from 'lucide-react'
import { Brand } from '@/components/brand'
import { OptionList } from '@/components/trip/option-list'
import { TripDetails } from '@/components/trip/trip-details'
import type { TripPlanner } from '@/hooks/use-trip-planner'
import { DirectionsBar } from './directions-bar'
import { TripForm } from './trip-form'
import { TripSummary } from './trip-summary'

interface PlannerPanelProps {
  planner: TripPlanner
  /** In the mobile sheet the brand floats over the map instead, so the peek shows the search. */
  showBrand?: boolean
  /** Called when a search field gains focus, e.g. so the mobile sheet can expand. */
  onSearchFocus?: () => void
  /**
   * Whether the Directions button sits in a footer at the bottom of the panel. A half-open
   * mobile sheet hides its own bottom, so there it goes under the selected option instead.
   */
  inlineActions?: boolean
}

function OptionsSkeleton() {
  return (
    <div aria-hidden className="flex flex-col gap-1">
      {[0, 1, 2].map((i) => (
        <div key={i} className="flex items-center gap-3 p-3">
          <div className="size-12 animate-pulse rounded-lg bg-muted" />
          <div className="flex-1 space-y-2">
            <div className="h-4 w-2/5 animate-pulse rounded bg-muted" />
            <div className="h-3 w-3/5 animate-pulse rounded bg-muted" />
          </div>
          <div className="h-4 w-12 animate-pulse rounded bg-muted" />
        </div>
      ))}
    </div>
  )
}

function Results({ planner, inlineActions }: { planner: TripPlanner; inlineActions: boolean }) {
  const { state, dispatch, options } = planner
  const { plan } = state

  if (plan.status === 'idle') return null
  if (plan.status === 'loading') {
    return (
      <section aria-label="Route options" aria-busy="true">
        <p className="sr-only" role="status">
          Finding routes…
        </p>
        <OptionsSkeleton />
      </section>
    )
  }
  if (plan.status === 'error') {
    return (
      <p role="alert" className="rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive">
        {plan.message}
      </p>
    )
  }
  if (options.length === 0) {
    return (
      <div role="status" className="rounded-lg bg-muted px-4 py-6 text-center text-sm">
        <p className="font-medium">No routes found</p>
        <p className="mt-1 text-muted-foreground">
          Try a different time, or a nearby stop or landmark.
        </p>
      </div>
    )
  }
  return (
    <section aria-labelledby="options-heading" className="flex flex-col gap-3">
      <h2 id="options-heading" className="text-lg font-bold tracking-tight">
        Choose a route
      </h2>
      <OptionList
        options={options}
        selectedId={state.selectedId}
        onSelect={(id) => dispatch({ type: 'select', id })}
        onDirections={inlineActions ? undefined : () => dispatch({ type: 'showDetails' })}
      />
      {plan.response.notices.length > 0 && (
        <div className="flex gap-2 rounded-lg bg-muted px-3 py-2.5 text-xs text-muted-foreground">
          <Info className="mt-px size-3.5 shrink-0" aria-hidden />
          <ul className="space-y-1">
            {plan.response.notices.map((notice) => (
              <li key={notice}>{notice}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}

function Attribution() {
  return (
    <footer className="mt-auto space-y-1 pt-4 text-xs text-muted-foreground">
      <p>
        Transit data:{' '}
        <a className="underline underline-offset-2" href="https://otd.delhi.gov.in" target="_blank" rel="noreferrer">
          Open Transit Data, Transport Dept., GNCTD
        </a>
        . Map and places: ©{' '}
        <a className="underline underline-offset-2" href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">
          OpenStreetMap
        </a>{' '}
        contributors.
      </p>
    </footer>
  )
}

/**
 * The planner's contents, shared by the mobile sheet and the desktop panel: the trip form
 * with route options below it, or the step-by-step directions for one option.
 */
export function PlannerPanel({
  planner,
  showBrand = true,
  onSearchFocus,
  inlineActions = true,
}: PlannerPanelProps) {
  const { state, dispatch, selected } = planner
  const padding = 'px-5 pb-[max(1.25rem,env(safe-area-inset-bottom))]'

  if (state.view === 'details' && selected) {
    return (
      <div className={`flex min-h-full flex-col gap-4 pt-2 lg:pt-4 ${padding}`}>
        <button
          type="button"
          onClick={() => dispatch({ type: 'back' })}
          className="-ml-2 inline-flex items-center gap-1.5 self-start rounded-full px-2 py-1.5 text-sm font-medium hover:bg-muted"
        >
          <ArrowLeft className="size-4" aria-hidden />
          All routes
        </button>
        <h2 className="sr-only">Directions: {selected.title}</h2>
        <TripDetails option={selected} />
        <Attribution />
      </div>
    )
  }

  const brand = showBrand && (
    <header>
      <Brand />
    </header>
  )

  if (state.view === 'options') {
    return (
      <div className={`flex min-h-full flex-col gap-5 pt-2 lg:pt-5 ${padding}`}>
        {brand}
        <TripSummary planner={planner} />
        <Results planner={planner} inlineActions={inlineActions} />
        {inlineActions && (
          <DirectionsBar planner={planner} className="sticky bottom-0 -mx-5 mt-auto" />
        )}
      </div>
    )
  }

  const hasRoutes = state.plan.status === 'ready' && state.origin && state.destination

  return (
    <div className={`flex min-h-full flex-col gap-5 pt-2 lg:pt-5 ${padding}`}>
      {brand}
      <section aria-labelledby="planner-heading" className="flex flex-col gap-4">
        <h1 id="planner-heading" className="font-heading text-[1.75rem] leading-tight font-bold tracking-tight">
          Where to?
        </h1>
        <TripForm planner={planner} onFieldFocus={onSearchFocus} />
        {hasRoutes && (
          <button
            type="button"
            onClick={() => dispatch({ type: 'showOptions' })}
            className="h-12 rounded-lg bg-foreground text-base font-semibold text-background hover:bg-foreground/85"
          >
            See routes
          </button>
        )}
      </section>
      <Attribution />
    </div>
  )
}
