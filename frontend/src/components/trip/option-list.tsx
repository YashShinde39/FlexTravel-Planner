import { ChevronRight } from 'lucide-react'
import { Fragment } from 'react'
import type { Leg, TripOption } from '@/lib/api/client'
import { formatDuration, formatFare, formatTime } from '@/lib/format'
import { cn } from '@/lib/utils'
import { ModeIcon } from './mode-icon'

const LABELS: Record<TripOption['labels'][number], string> = {
  fastest: 'Fastest',
  cheapest: 'Cheapest',
  fewest_changes: 'Fewest changes',
  least_walking: 'Least walking',
}

/** Walk 4 min › 216 › 522 SPL: the shape of a journey at a glance. */
export function LegChain({ legs }: { legs: Leg[] }) {
  return (
    <span className="flex flex-wrap items-center gap-1">
      {legs.map((leg, index) => (
        <Fragment key={index}>
          {index > 0 && <ChevronRight className="size-3 text-muted-foreground" aria-hidden />}
          {leg.route ? (
            <span className="inline-flex items-center gap-1 rounded-md bg-foreground px-1.5 py-0.5 text-xs font-semibold text-background">
              <ModeIcon mode={leg.mode} className="size-3" />
              {leg.route.code}
            </span>
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
  onDirections,
}: {
  option: TripOption
  selected: boolean
  onSelect: () => void
  onDirections?: () => void
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
          'flex w-full items-center gap-3 rounded-xl border-2 border-transparent p-3 text-left transition-colors hover:bg-muted',
          selected && 'border-foreground hover:bg-transparent',
        )}
      >
        <span className="grid size-12 shrink-0 place-items-center rounded-lg bg-muted">
          <ModeIcon mode={iconMode} className="size-6" />
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <span className="truncate font-semibold">{option.title}</span>
            {option.labels.map((label) => (
              <span
                key={label}
                className="rounded-sm bg-emerald-600 px-1.5 py-px text-[0.7rem] font-semibold text-white dark:bg-emerald-500 dark:text-black"
              >
                {LABELS[label]}
              </span>
            ))}
          </span>
          <span className="mt-0.5 block text-sm text-muted-foreground tabular-nums">
            {formatTime(option.departure, estimated)} – {formatTime(option.arrival, estimated)}
            {option.later_departures.length > 0 && (
              <> · also {option.later_departures.map((t) => formatTime(t)).join(', ')}</>
            )}
          </span>
          {option.kind === 'transit' && (
            <span className="mt-1.5 block">
              <LegChain legs={option.legs} />
            </span>
          )}
        </span>
        <span className="shrink-0 text-right">
          <span className="block font-semibold tabular-nums">
            {formatDuration(option.duration_s)}
          </span>
          <span className="block text-sm text-muted-foreground tabular-nums">
            {option.fare ? formatFare(option.fare) : 'Free'}
          </span>
        </span>
      </button>
      {selected && onDirections && (
        <button
          type="button"
          onClick={onDirections}
          className="mt-1 mb-2 h-11 w-full rounded-lg bg-foreground text-base font-semibold text-background hover:bg-foreground/85"
        >
          Directions
        </button>
      )}
    </li>
  )
}

interface OptionListProps {
  options: TripOption[]
  selectedId: string | null
  onSelect: (id: string) => void
  /** Shows a Directions button under the selected option (phones; desktop has a footer). */
  onDirections?: () => void
}

export function OptionList({ options, selectedId, onSelect, onDirections }: OptionListProps) {
  return (
    <ul aria-label="Route options" className="flex flex-col gap-1">
      {options.map((option) => (
        <OptionRow
          key={option.id}
          option={option}
          selected={option.id === selectedId}
          onSelect={() => onSelect(option.id)}
          onDirections={onDirections}
        />
      ))}
    </ul>
  )
}
