import {
  BusFront,
  CarTaxiFront,
  Footprints,
  type LucideProps,
  TrainFront,
  TramFront,
} from 'lucide-react'
import type { Leg, TripOption } from '@/lib/api/client'

/** An auto-rickshaw in Lucide's style (24px grid, 2px round strokes); Lucide has none. */
export function AutoRickshaw({ strokeWidth = 2, ...props }: LucideProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      {/* canopy, cab and the single front wheel + two rear wheels seen from the side */}
      <path d="M4 15V9a4 4 0 0 1 4-4h6l4 5" />
      <path d="M4 15h2m4 0h5m4 0h1v-3a2 2 0 0 0-2-2h-4V5" />
      <circle cx="8" cy="16" r="2" />
      <circle cx="17" cy="16" r="2" />
    </svg>
  )
}

type IconMode = Leg['mode'] | TripOption['kind']

const ICONS: Record<IconMode, (props: LucideProps) => React.ReactNode> = {
  walk: Footprints,
  bus: BusFront,
  metro: TramFront,
  rail: TrainFront,
  auto: AutoRickshaw,
  cab: CarTaxiFront,
  transit: BusFront,
}

export function ModeIcon({ mode, ...props }: LucideProps & { mode: IconMode }) {
  const Icon = ICONS[mode]
  return <Icon aria-hidden {...props} />
}
