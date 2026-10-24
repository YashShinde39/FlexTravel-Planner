import type { TripPlanner } from '@/hooks/use-trip-planner'
import { cn } from '@/lib/utils'

/** The main action pinned under the options, like a ride app's "Choose UberX" button. */
export function DirectionsBar({ planner, className }: { planner: TripPlanner; className?: string }) {
  const { selected, dispatch } = planner
  if (!selected) return null
  return (
    <div
      className={cn(
        'border-t bg-background/95 px-5 pt-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] backdrop-blur',
        className,
      )}
    >
      <button
        type="button"
        onClick={() => dispatch({ type: 'showDetails' })}
        className="mx-auto block h-11 w-full max-w-2xl truncate rounded-lg bg-foreground px-4 text-[0.9375rem] font-medium text-background hover:bg-foreground/85"
      >
        Directions for {selected.title}
      </button>
    </div>
  )
}
