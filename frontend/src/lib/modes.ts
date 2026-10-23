import type { Leg } from '@/lib/api/client'

export const MODE_NAMES: Record<Leg['mode'], string> = {
  walk: 'Walk',
  bus: 'Bus',
  metro: 'Metro',
  rail: 'Train',
  auto: 'Auto',
  cab: 'Cab',
}
