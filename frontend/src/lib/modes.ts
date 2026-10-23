import type { Leg } from '@/lib/api/client'

export const MODE_NAMES: Record<Leg['mode'], string> = {
  walk: 'Walk',
  bus: 'Bus',
  metro: 'Metro',
  rail: 'Train',
  auto: 'Auto',
  cab: 'Cab',
}

/** "#RRGGBB" for a Metro line's colour, from the API's "RRGGBB"; none for buses. */
export function lineColor(leg: Leg): string | undefined {
  return leg.route?.color ? `#${leg.route.color}` : undefined
}
