import { ArrowDownUp, ChevronDown, Clock } from 'lucide-react'
import { useState } from 'react'
import type { TripPlanner } from '@/hooks/use-trip-planner'
import { PlaceField } from './place-field'

export function OriginMarker() {
  return <span className="block size-2.5 rounded-full bg-foreground" aria-hidden />
}

export function DestinationMarker() {
  return <span className="block size-2.5 bg-foreground" aria-hidden />
}

/** Now in Delhi as `YYYY-MM-DDTHH:mm`, the format of a datetime-local input. */
function delhiNow(): string {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Kolkata',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  }).formatToParts(new Date())
  const get = (type: string) => parts.find((p) => p.type === type)?.value
  return `${get('year')}-${get('month')}-${get('day')}T${get('hour')}:${get('minute')}`
}

export function DepartureTime({ planner }: { planner: TripPlanner }) {
  const { state, dispatch } = planner
  const [open, setOpen] = useState(false)
  const label = state.departAt
    ? `Leave ${new Date(`${state.departAt}:00+05:30`).toLocaleString('en-IN', {
        timeZone: 'Asia/Kolkata',
        weekday: 'short',
        hour: '2-digit',
        minute: '2-digit',
        hourCycle: 'h23',
      })}`
    : 'Leave now'

  return (
    <div>
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
        className="inline-flex h-9 items-center gap-2 rounded-full bg-muted px-3.5 text-sm font-medium hover:bg-accent"
      >
        <Clock className="size-4" aria-hidden />
        {label}
        <ChevronDown className="size-4 transition-transform in-aria-expanded:rotate-180" aria-hidden />
      </button>
      {open && (
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <button
            type="button"
            aria-pressed={!state.departAt}
            onClick={() => {
              dispatch({ type: 'setDepartAt', departAt: null })
              setOpen(false)
            }}
            className="h-9 rounded-full border px-3.5 text-sm font-medium aria-pressed:border-foreground aria-pressed:bg-foreground aria-pressed:text-background"
          >
            Now
          </button>
          <label className="sr-only" htmlFor="depart-at">
            Leave at
          </label>
          <input
            id="depart-at"
            type="datetime-local"
            value={state.departAt ?? delhiNow()}
            min={delhiNow()}
            onChange={(event) =>
              dispatch({ type: 'setDepartAt', departAt: event.target.value || null })
            }
            className="h-9 rounded-full border px-3.5 text-sm font-medium outline-none focus:ring-2 focus:ring-foreground"
          />
        </div>
      )}
    </div>
  )
}

interface TripFormProps {
  planner: TripPlanner
  onFieldFocus?: () => void
}

export function TripForm({ planner, onFieldFocus }: TripFormProps) {
  const { state, dispatch } = planner
  const canSwap = Boolean(state.origin || state.destination)

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <div className="relative flex min-w-0 flex-1 flex-col gap-2">
          {/* The line joining the start dot and the end square, as in ride apps. */}
          <span
            className="pointer-events-none absolute top-6 bottom-6 left-[1.28rem] z-10 w-px bg-foreground/50"
            aria-hidden
          />
          <PlaceField
            key={`from-${state.swaps}`}
            label="From"
            placeholder="From: stop, station or landmark"
            value={state.origin}
            onChange={(place) => dispatch({ type: 'setOrigin', place })}
            marker={<OriginMarker />}
            onFocus={onFieldFocus}
          />
          <PlaceField
            key={`to-${state.swaps}`}
            label="To"
            placeholder="Where to?"
            value={state.destination}
            onChange={(place) => dispatch({ type: 'setDestination', place })}
            marker={<DestinationMarker />}
            onFocus={onFieldFocus}
          />
        </div>
        <button
          type="button"
          disabled={!canSwap}
          onClick={() => dispatch({ type: 'swap' })}
          aria-label="Swap start and destination"
          className="grid size-10 shrink-0 place-items-center rounded-full bg-muted hover:bg-accent disabled:opacity-40"
        >
          <ArrowDownUp className="size-4" aria-hidden />
        </button>
      </div>
      <DepartureTime planner={planner} />
    </div>
  )
}
