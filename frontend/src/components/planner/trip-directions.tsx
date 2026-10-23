import { ArrowLeft } from 'lucide-react'
import { TripDetails } from '@/components/trip/trip-details'
import type { TripPlanner } from '@/hooks/use-trip-planner'

/** One option's step-by-step directions, with a way back to the other options. */
export function TripDirections({ planner }: { planner: TripPlanner }) {
  const { selected, dispatch } = planner
  if (!selected) return null
  return (
    <div className="flex flex-col gap-4">
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
    </div>
  )
}
