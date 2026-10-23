import { ArrowDownUp, Flag, MapPin } from 'lucide-react'
import { Brand } from '@/components/brand'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

interface PlannerPanelProps {
  /** In the mobile sheet the brand floats over the map instead, so the peek shows the search. */
  showBrand?: boolean
  /** Called when a search field gains focus, e.g. so the mobile sheet can expand. */
  onSearchFocus?: () => void
}

/**
 * The planner's contents, shared by the mobile sheet and the desktop panel.
 * Search fields are visual only for now; trip search is wired up in the next PR.
 */
export function PlannerPanel({ showBrand = true, onSearchFocus }: PlannerPanelProps) {
  return (
    <div className="flex min-h-full flex-col gap-6 px-5 pt-2 pb-[max(1.25rem,env(safe-area-inset-bottom))] lg:pt-5">
      {showBrand && (
        <header>
          <Brand />
        </header>
      )}

      <section aria-labelledby="planner-heading" className="flex flex-col gap-4">
        <div>
          <h1 id="planner-heading" className="font-heading text-2xl font-semibold tracking-tight">
            Where to?
          </h1>
          <p className="mt-1 hidden text-sm text-muted-foreground sm:block lg:block">
            Compare metro, bus and auto routes by time, changes and fare.
          </p>
        </div>

        <form className="relative flex flex-col gap-2" onSubmit={(event) => event.preventDefault()}>
          <label className="sr-only" htmlFor="trip-from">
            From
          </label>
          <div className="relative">
            <MapPin
              className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden
            />
            <Input
              id="trip-from"
              placeholder="From: stop, station or landmark"
              className="h-11 pr-12 pl-9"
              autoComplete="off"
              onFocus={onSearchFocus}
            />
          </div>
          <label className="sr-only" htmlFor="trip-to">
            To
          </label>
          <div className="relative">
            <Flag
              className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden
            />
            <Input
              id="trip-to"
              placeholder="To: stop, station or landmark"
              className="h-11 pr-12 pl-9"
              autoComplete="off"
              onFocus={onSearchFocus}
            />
          </div>
          <Button
            type="button"
            variant="outline"
            size="icon"
            className="absolute top-1/2 right-2 size-8 -translate-y-1/2 rounded-full bg-background"
            aria-label="Swap start and destination"
          >
            <ArrowDownUp className="size-4" aria-hidden />
          </Button>
        </form>
      </section>

      <footer className="mt-auto space-y-1 text-xs text-muted-foreground">
        <p>Bus times are approximate: the official bus timetable dates from 2023.</p>
        <p>
          Transit data:{' '}
          <a className="underline underline-offset-2" href="https://otd.delhi.gov.in" target="_blank" rel="noreferrer">
            Open Transit Data, Transport Dept., GNCTD
          </a>
        </p>
      </footer>
    </div>
  )
}
