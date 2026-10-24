import { ChevronRight } from 'lucide-react'
import { Fragment } from 'react'
import type { Leg, TripOption } from '@/lib/api/client'
import { formatDuration, formatFare, formatTime } from '@/lib/format'
import { cn } from '@/lib/utils'
import { ModeIcon } from './mode-icon'
import { RouteBadge } from './route-badge'

const LABELS: Record<TripOption['labels'][number], string> = {
  fastest: 'Fastest',
  cheapest: 'Cheapest',
  fewest_changes: 'Fewest changes',
  least_walking: 'Least walking',
}

/** Walk 4 min › 216 › 522 SPL: the shape of a journey at a glance. Walks inside a
 * station (in, out, or between lines) are left out: they aren't a choice. */
export function LegChain({ legs }: { legs: Leg[] }) {
  const shown = legs.filter((leg) => leg.mode !== 'walk' || leg.start.name !== leg.end.name)
  return (
    <span className="flex flex-wrap items-center gap-1">
      {shown.map((leg, index) => (
        <Fragment key={index}>
          {index > 0 && (
            <ChevronRight className="size-3 text-muted-foreground/60" aria-hidden />
          )}
          {leg.route ? (
            <RouteBadge leg={leg} className="px-1.5 py-px text-[0.6875rem]" />
          ) : (
            <span className="inline-flex items-center gap-0.5 text-xs text-muted-foreground">
              <ModeIcon mode={leg.mode} className="size-3.5" />
              {leg.mode === 'walk' && formatDuration(leg.duration_s)}
            </span>
          )}
        </Fragment>
      ))}
    </span>
  )
}

function OptionRow({
  option,
  selected,
  onSelect,
}: {
  option: TripOption
  selected: boolean
  onSelect: () => void
}) {
  const estimated = option.legs.some((leg) => leg.times_estimated)
  const firstRide = option.legs.find((leg) => leg.mode !== 'walk')
  const iconMode = option.kind === 'transit' ? (firstRide?.mode ?? 'bus') : option.kind

  return (
    <li>
      <button
        type="button"
        aria-pressed={selected}
        onClick={onSelect}
        className={cn(
          'flex w-full items-start gap-3 rounded-lg px-3 py-3 text-left transition-colors hover:bg-muted/70',
          selected && 'bg-background ring-[1.5px] ring-foreground ring-inset hover:bg-background',
        )}
      >
        <span className="mt-0.5 grid size-10 shrink-0 place-items-center rounded-md bg-muted">
          <ModeIcon mode={iconMode} className="size-5" strokeWidth={1.75} />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block truncate text-[0.9375rem] font-semibold">{option.title}</span>
          {option.labels.length > 0 && (
            <span className="block text-xs font-medium text-emerald-700 dark:text-emerald-400">
              {option.labels.map((label) => LABELS[label]).join(' · ')}
            </span>
          )}
          <span className="mt-0.5 block text-[0.8125rem] text-muted-foreground tabular-nums">
            {formatTime(option.departure, estimated)} – {formatTime(option.arrival, estimated)}
          </span>
          {option.kind === 'transit' && (
            <span className="mt-2 block">
              <LegChain legs={option.legs} />
            </span>
          )}
          {option.later_departures.length > 0 && (
            <span className="mt-1.5 block text-xs text-muted-foreground tabular-nums">
              Also at {option.later_departures.map((t) => formatTime(t)).join(', ')}
            </span>
          )}
        </span>
        <span className="shrink-0 text-right">
          <span className="block text-[0.9375rem] font-semibold tabular-nums">
            {formatDuration(option.duration_s)}
          </span>
          <span className="mt-0.5 block text-[0.8125rem] text-muted-foreground tabular-nums">
            {option.fare ? formatFare(option.fare) : 'Free'}
          </span>
        </span>
      </button>
    </li>
  )
}

interface OptionListProps {
  options: TripOption[]
  selectedId: string | null
  onSelect: (id: string) => void
}

export function OptionList({ options, selectedId, onSelect }: OptionListProps) {
  return (
    <ul aria-label="Route options" className="flex flex-col gap-0.5">
      {options.map((option) => (
        <OptionRow
          key={option.id}
          option={option}
          selected={option.id === selectedId}
          onSelect={() => onSelect(option.id)}
        />
      ))}
    </ul>
  )
}
