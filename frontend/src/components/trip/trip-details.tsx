import { ChevronDown } from 'lucide-react'
import type { Leg, TripOption } from '@/lib/api/client'
import { formatDistance, formatDuration, formatFare, formatTime } from '@/lib/format'
import { cn } from '@/lib/utils'
import { lineColor, MODE_NAMES } from '@/lib/modes'
import { ModeIcon } from './mode-icon'
import { RouteBadge } from './route-badge'

/** A collapsible list, closed by default, e.g. a bus's intermediate stops. */
function More({ summary, items }: { summary: string; items: string[] }) {
  if (items.length === 0) return null
  return (
    <details className="group mt-1.5 text-sm">
      <summary className="inline-flex cursor-pointer list-none items-center gap-1 text-muted-foreground hover:text-foreground [&::-webkit-details-marker]:hidden">
        {summary}
        <ChevronDown className="size-4 transition-transform group-open:rotate-180" aria-hidden />
      </summary>
      <ol className="mt-1.5 space-y-1 text-muted-foreground">
        {items.map((item, index) => (
          <li key={index}>{item}</li>
        ))}
      </ol>
    </details>
  )
}

/** A walk that stays inside one station: into it, out of it, or between two lines. */
type StationWalk = { kind: 'enter' | 'leave' } | { kind: 'change'; to: Leg }

function stationWalk(legs: Leg[], index: number): StationWalk | undefined {
  const [before, walk, after] = [legs[index - 1], legs[index], legs[index + 1]]
  if (walk.mode !== 'walk' || walk.start.name !== walk.end.name) return undefined
  if (before?.route && after?.route) return { kind: 'change', to: after }
  if (after?.route && after.start.name === walk.end.name) return { kind: 'enter' }
  if (before?.route && before.end.name === walk.start.name) return { kind: 'leave' }
  return undefined
}

function LegBody({ leg, inStation }: { leg: Leg; inStation?: StationWalk }) {
  if (inStation) {
    const what =
      inStation.kind === 'change'
        ? `Change to the ${inStation.to.route?.code}`
        : inStation.kind === 'enter'
          ? 'Into the station'
          : 'Out of the station'
    return (
      <p className="text-sm text-muted-foreground">
        {what} · {formatDuration(leg.duration_s)}
      </p>
    )
  }
  if (leg.mode === 'walk') {
    return (
      <>
        <p className="text-sm text-muted-foreground">
          Walk {formatDuration(leg.duration_s)} · {formatDistance(leg.distance_m)}
        </p>
        <More
          summary="Directions"
          items={leg.steps.map((s) => `${s.instruction} (${formatDistance(s.distance_m)})`)}
        />
      </>
    )
  }
  if (!leg.route) {
    // Auto or cab: one ride, door to door.
    return (
      <p className="text-sm text-muted-foreground">
        {MODE_NAMES[leg.mode]} · about {formatDuration(leg.duration_s)} ·{' '}
        {formatDistance(leg.distance_m)}
      </p>
    )
  }
  const stops = leg.intermediate_stops.length + 1
  return (
    <>
      <p className="flex flex-wrap items-center gap-2">
        <RouteBadge leg={leg} className="px-2 py-0.5 text-sm" />
        {leg.headsign && <span className="text-sm">towards {leg.headsign}</span>}
      </p>
      <p className="mt-1 text-sm text-muted-foreground">
        {stops} {stops === 1 ? 'stop' : 'stops'} · {formatDuration(leg.duration_s)}
      </p>
      <More
        summary={`${leg.intermediate_stops.length} stops in between`}
        items={leg.intermediate_stops.map((s) => s.name)}
      />
    </>
  )
}

/** One stop on the timeline: time, a node on the rail, and the place's name. */
function PlaceRow({
  time,
  name,
  estimated,
  terminal,
}: {
  time: string
  name: string
  estimated: boolean
  terminal?: 'start' | 'end'
}) {
  return (
    <li className="grid grid-cols-[3.5rem_1.5rem_1fr] items-center gap-x-2">
      <span className="text-sm font-medium tabular-nums">{formatTime(time, estimated)}</span>
      <span className="grid place-items-center">
        <span
          className={cn(
            'size-3 border-2 border-foreground bg-background',
            terminal === 'end' ? 'bg-foreground' : 'rounded-full',
            terminal === 'start' && 'bg-foreground',
          )}
          aria-hidden
        />
      </span>
      <span className="font-semibold">{name}</span>
    </li>
  )
}

function LegRow({ leg, inStation }: { leg: Leg; inStation?: StationWalk }) {
  const rail =
    leg.mode === 'walk'
      ? 'border-l-2 border-dotted border-muted-foreground'
      : 'border-l-4 border-foreground'
  return (
    <li className="grid grid-cols-[3.5rem_1.5rem_1fr] gap-x-2">
      <span className="grid place-items-start pt-3">
        <ModeIcon mode={leg.mode} className="size-4 text-muted-foreground" />
      </span>
      <span className="flex justify-center py-1">
        <span
          className={cn('h-full min-h-12', rail)}
          style={{ borderColor: lineColor(leg) }}
          aria-hidden
        />
      </span>
      <div className="py-3">
        <LegBody leg={leg} inStation={inStation} />
      </div>
    </li>
  )
}

export function TripDetails({ option }: { option: TripOption }) {
  const { legs } = option
  const estimated = (leg: Leg) => leg.times_estimated
  const fareNote = option.fare?.note
  const anyEstimated = legs.some(estimated)

  return (
    <div className="flex flex-col gap-5">
      <div>
        <p className="font-heading text-[1.75rem] leading-tight font-semibold tracking-tight">
          {formatDuration(option.duration_s)}
        </p>
        <p className="mt-1 text-sm text-muted-foreground">
          Arrive {formatTime(option.arrival, anyEstimated)}
          {option.fare && <> · {formatFare(option.fare)}</>}
          {option.transfers > 0 && (
            <> · {option.transfers} {option.transfers === 1 ? 'change' : 'changes'}</>
          )}
        </p>
      </div>

      <ol aria-label="Steps" className="flex flex-col">
        {legs.flatMap((leg, index) => [
          <PlaceRow
            key={`place-${index}`}
            time={leg.departure}
            name={leg.start.name}
            estimated={leg.times_estimated}
            terminal={index === 0 ? 'start' : undefined}
          />,
          <LegRow key={`leg-${index}`} leg={leg} inStation={stationWalk(legs, index)} />,
        ])}
        <PlaceRow
          time={option.arrival}
          name={legs[legs.length - 1].end.name}
          estimated={anyEstimated}
          terminal="end"
        />
      </ol>

      {(fareNote || anyEstimated) && (
        <div className="space-y-1 border-t pt-3 text-xs leading-relaxed text-muted-foreground">
          {anyEstimated && <p>Times marked ~ are estimates.</p>}
          {fareNote && <p>{fareNote}</p>}
        </div>
      )}
    </div>
  )
}
