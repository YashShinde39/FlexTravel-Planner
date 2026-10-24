import { ArrowRight, ChevronDown } from 'lucide-react'
import type { TripPlanner } from '@/hooks/use-trip-planner'
import { formatDeparture } from '@/lib/format'

/** The chosen trip in one box above the options, as "A → B" and when; tapping it edits the trip. */
export function TripSummary({ planner }: { planner: TripPlanner }) {
  const { state, dispatch } = planner
  const when = formatDeparture(state.departAt)
  return (
    <button
      type="button"
      onClick={() => dispatch({ type: 'back' })}
      aria-label={`Edit trip from ${state.origin?.name} to ${state.destination?.name}`}
      className="flex w-full items-center gap-3 rounded-lg border px-4 py-2.5 text-left hover:bg-muted/70"
    >
      <span className="min-w-0 flex-1">
        <span className="flex items-center gap-1.5 text-[0.9375rem] font-medium">
          <span className="truncate">{state.origin?.name}</span>
          <ArrowRight className="size-4 shrink-0" aria-hidden />
          <span className="truncate">{state.destination?.name}</span>
        </span>
        <span className="block text-[0.8125rem] text-muted-foreground">{when}</span>
      </span>
      <ChevronDown className="size-4 shrink-0 text-muted-foreground" aria-hidden />
    </button>
  )
}
