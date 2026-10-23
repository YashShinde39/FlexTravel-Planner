import { Pencil } from 'lucide-react'
import type { TripPlanner } from '@/hooks/use-trip-planner'
import { DestinationMarker, DepartureTime, OriginMarker } from './trip-form'

/** The chosen trip in two lines, shown above the options; tapping it edits the trip. */
export function TripSummary({ planner }: { planner: TripPlanner }) {
  const { state, dispatch } = planner
  return (
    <div className="flex flex-col gap-3">
      <button
        type="button"
        onClick={() => dispatch({ type: 'back' })}
        aria-label={`Edit trip from ${state.origin?.name} to ${state.destination?.name}`}
        className="group relative flex items-center gap-3 rounded-xl bg-muted px-4 py-3 text-left hover:bg-accent"
      >
        <span className="relative flex flex-col items-center gap-[1.15rem] self-stretch py-1.5">
          <span className="absolute top-3 bottom-3 w-px bg-foreground/50" aria-hidden />
          <OriginMarker />
          <DestinationMarker />
        </span>
        <span className="min-w-0 flex-1 space-y-1.5">
          <span className="block truncate font-medium">{state.origin?.name}</span>
          <span className="block truncate font-medium">{state.destination?.name}</span>
        </span>
        <Pencil className="size-4 shrink-0 text-muted-foreground group-hover:text-foreground" aria-hidden />
      </button>
      <DepartureTime planner={planner} />
    </div>
  )
}
