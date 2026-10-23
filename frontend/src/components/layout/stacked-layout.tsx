import { ArrowLeft } from 'lucide-react'
import { type ReactNode, useRef, useState } from 'react'
import { flushSync } from 'react-dom'
import { Brand } from '@/components/brand'
import { PlannerMap } from '@/components/map/planner-map'
import { Attribution } from '@/components/planner/attribution'
import { DirectionsBar } from '@/components/planner/directions-bar'
import { RouteOptions } from '@/components/planner/route-options'
import { SearchScreen } from '@/components/planner/search-screen'
import { TripDirections } from '@/components/planner/trip-directions'
import {
  DepartureTime,
  DestinationMarker,
  OriginMarker,
} from '@/components/planner/trip-form'
import { TripSummary } from '@/components/planner/trip-summary'
import type { TripPlanner } from '@/hooks/use-trip-planner'
import { cn } from '@/lib/utils'

type Field = 'from' | 'to'

// Keeps fitted routes clear of the button floating at the top of the map, and of the
// panel's rounded edge and the map's credit at the bottom.
const MAP_PADDING = { top: 56, right: 0, bottom: 28, left: 0 }

/** Looks like a field; tapping it opens the search screen with that field focused. */
function FieldButton({
  label,
  value,
  placeholder,
  marker,
  onClick,
}: {
  label: string
  value: string | undefined
  placeholder: string
  marker: ReactNode
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={value ? `${label}: ${value}` : label}
      className="relative flex h-12 w-full items-center rounded-lg bg-muted pr-4 pl-10 text-left text-base hover:bg-accent"
    >
      <span className="absolute top-1/2 left-4 -translate-y-1/2">{marker}</span>
      <span className={cn('truncate', value ? 'font-medium' : 'text-muted-foreground')}>
        {value ?? placeholder}
      </span>
    </button>
  )
}

/** A round button floating over the map's top-left corner, as in ride apps. */
function MapButton({ label, onClick, children }: { label: string; onClick: () => void; children: ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      className="absolute top-[max(0.75rem,env(safe-area-inset-top))] left-3 z-10 grid size-11 place-items-center rounded-full bg-background shadow-md hover:bg-muted"
    >
      {children}
    </button>
  )
}

/**
 * Phones and tablets held upright, as on Uber's site: the map on top and the planner in a
 * fixed panel below it. Before a search the panel is a short "Where to?" card; tapping a
 * field opens a full-screen search. With routes, the map shrinks to the top 40% and the
 * options fill the rest, with Directions pinned at the bottom.
 */
export function StackedLayout({ planner }: { planner: TripPlanner }) {
  const { state, dispatch } = planner
  const { view } = state
  const [searching, setSearching] = useState<Field | null>(null)
  const fromRef = useRef<HTMLInputElement>(null)
  const toRef = useRef<HTMLInputElement>(null)

  // Once both places are chosen the planner moves on to the options; the search screen
  // closes with it. Adjusted while rendering (React's pattern), not in an effect.
  if (searching && view !== 'search') setSearching(null)

  function openSearch(field: Field) {
    // Render the screen now, then focus within this same tap so the keyboard comes up.
    flushSync(() => setSearching(field))
    ;(field === 'from' ? fromRef : toRef).current?.focus()
  }

  function onPlaceChosen(field: Field) {
    // Go straight on to whichever place is still missing.
    if (field === 'from' && !state.destination) toRef.current?.focus()
    if (field === 'to' && !state.origin) fromRef.current?.focus()
  }

  const hasRoutes = view === 'search' && state.plan.status === 'ready'

  return (
    <main className="flex h-dvh flex-col overflow-hidden bg-background">
      <div
        className={cn(
          'relative [&_.maplibregl-ctrl-bottom-right]:mb-4',
          view === 'search' ? 'min-h-0 flex-1' : 'h-[max(40dvh,260px)] shrink-0',
        )}
      >
        <PlannerMap planner={planner} padding={MAP_PADDING} frameKey={view} />
        {view === 'search' ? (
          <Brand className="absolute top-[max(0.75rem,env(safe-area-inset-top))] left-3 z-10 rounded-full border bg-background/90 py-1 pr-3 pl-1 shadow-md backdrop-blur" />
        ) : (
          <MapButton
            label={view === 'details' ? 'Back to all routes' : 'Edit trip'}
            onClick={() => dispatch({ type: 'back' })}
          >
            <ArrowLeft className="size-5" aria-hidden />
          </MapButton>
        )}
      </div>

      <section
        aria-label="Trip planner"
        className={cn(
          'relative z-10 -mt-4 flex flex-col rounded-t-2xl bg-background shadow-[0_-8px_30px_rgb(0_0_0/0.12)]',
          view === 'search' ? 'shrink-0' : 'min-h-0 flex-1',
        )}
      >
        {view === 'search' && (
          <div className="mx-auto flex w-full max-w-2xl flex-col gap-4 px-5 pt-5 pb-[max(1.25rem,env(safe-area-inset-bottom))]">
            <h1 className="font-heading text-[1.75rem] leading-tight font-bold tracking-tight">
              Where to?
            </h1>
            <div className="relative flex flex-col gap-2">
              <span
                className="pointer-events-none absolute top-6 bottom-6 left-[1.28rem] z-10 w-px bg-foreground/50"
                aria-hidden
              />
              <FieldButton
                label="From"
                value={state.origin?.name}
                placeholder="Where from?"
                marker={<OriginMarker />}
                onClick={() => openSearch('from')}
              />
              <FieldButton
                label="To"
                value={state.destination?.name}
                placeholder="Where to?"
                marker={<DestinationMarker />}
                onClick={() => openSearch('to')}
              />
            </div>
            <DepartureTime planner={planner} />
            {hasRoutes && (
              <button
                type="button"
                onClick={() => dispatch({ type: 'showOptions' })}
                className="h-12 rounded-lg bg-foreground text-base font-semibold text-background hover:bg-foreground/85"
              >
                See routes
              </button>
            )}
          </div>
        )}

        {view === 'options' && (
          <>
            <h2 className="shrink-0 border-b py-3.5 text-center text-lg font-bold">Choose a route</h2>
            <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
              <div className="mx-auto flex w-full max-w-2xl flex-col gap-4 px-4 py-4">
                <TripSummary planner={planner} />
                <RouteOptions planner={planner} />
                <Attribution />
              </div>
            </div>
            <DirectionsBar planner={planner} />
          </>
        )}

        {view === 'details' && (
          <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
            <div className="mx-auto flex w-full max-w-2xl flex-col gap-4 px-5 pt-3 pb-[max(1.25rem,env(safe-area-inset-bottom))]">
              <TripDirections planner={planner} />
              <Attribution />
            </div>
          </div>
        )}
      </section>

      <SearchScreen
        planner={planner}
        open={searching !== null}
        onClose={() => setSearching(null)}
        fromRef={fromRef}
        toRef={toRef}
        onPlaceChosen={onPlaceChosen}
      />
    </main>
  )
}
