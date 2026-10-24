import { Info } from 'lucide-react'
import { OptionList } from '@/components/trip/option-list'
import type { TripPlanner } from '@/hooks/use-trip-planner'

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

/** The ways to make the trip, or what's happening instead: loading, an error, or none found. */
export function RouteOptions({ planner }: { planner: TripPlanner }) {
  const { state, dispatch, options } = planner
  const { plan } = state

  if (plan.status === 'idle') return null
  if (plan.status === 'loading') {
    return (
      <div aria-busy="true">
        <p className="sr-only" role="status">
          Finding routes…
        </p>
        <OptionsSkeleton />
      </div>
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
    <div className="flex flex-col gap-3">
      <OptionList
        options={options}
        selectedId={state.selectedId}
        onSelect={(id) => dispatch({ type: 'select', id })}
      />
      {plan.response.notices.length > 0 && (
        <div className="flex gap-2 px-3 pt-1 text-xs leading-relaxed text-muted-foreground">
          <Info className="mt-0.5 size-3.5 shrink-0" aria-hidden />
          <ul className="space-y-1">
            {plan.response.notices.map((notice) => (
              <li key={notice}>{notice}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
