import type { TripPlanner } from '@/hooks/use-trip-planner'
import { TripForm } from './trip-form'

/** "Where to?" with the trip form: the planner's first screen on desktops and sideways phones. */
export function SearchCard({ planner }: { planner: TripPlanner }) {
  const { state, dispatch } = planner
  const hasRoutes = state.view === 'search' && state.plan.status === 'ready'
  return (
    <section aria-labelledby="planner-heading" className="flex flex-col gap-4">
      <h1 id="planner-heading" className="font-heading text-2xl font-bold tracking-tight">
        Where to?
      </h1>
      <TripForm planner={planner} />
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
  )
}
