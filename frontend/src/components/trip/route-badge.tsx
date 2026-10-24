import type { Leg } from '@/lib/api/client'
import { lineColor } from '@/lib/modes'
import { cn } from '@/lib/utils'
import { ModeIcon } from './mode-icon'

/**
 * A ride's route as a badge: a Metro line in its own colour ("Yellow Line"), a bus in
 * black ("270"), like the signs at stations and stops.
 */
export function RouteBadge({ leg, className }: { leg: Leg; className?: string }) {
  if (!leg.route) return null
  const background = lineColor(leg)
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-[0.25rem] leading-normal font-semibold',
        !background && 'bg-foreground text-background',
        className,
      )}
      style={
        background
          ? { backgroundColor: background, color: `#${leg.route.text_color ?? 'FFFFFF'}` }
          : undefined
      }
    >
      <ModeIcon mode={leg.mode} className="size-[1em]" />
      {leg.route.code}
    </span>
  )
}
