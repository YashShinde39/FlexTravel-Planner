import type { Fare } from '@/lib/api/client'

// Journeys are in Delhi, so times show in Delhi time wherever the visitor's phone is set.
const clock = new Intl.DateTimeFormat('en-IN', {
  hour: '2-digit',
  minute: '2-digit',
  hourCycle: 'h23',
  timeZone: 'Asia/Kolkata',
})

/** "09:04", or "~09:04" for estimated times (ADR-0007). */
export function formatTime(iso: string, estimated = false): string {
  return `${estimated ? '~' : ''}${clock.format(new Date(iso))}`
}

/** "45 min", "1 h 5 min", "2 h". */
export function formatDuration(seconds: number): string {
  const minutes = Math.max(1, Math.round(seconds / 60))
  if (minutes < 60) return `${minutes} min`
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  return rest ? `${hours} h ${rest} min` : `${hours} h`
}

/** "350 m", "1.2 km", "12 km". */
export function formatDistance(metres: number): string {
  if (metres < 1000) return `${Math.round(metres / 10) * 10} m`
  const km = metres / 1000
  return `${km < 10 ? km.toFixed(1) : Math.round(km)} km`
}

/** "₹104" or "₹10–20". */
export function formatFare(fare: Fare): string {
  return fare.min === fare.max ? `₹${fare.min}` : `₹${fare.min}–${fare.max}`
}

/** Minutes until a time, for "leaves in 4 min". Negative if it's already gone. */
export function minutesUntil(iso: string, now: Date = new Date()): number {
  return Math.round((new Date(iso).getTime() - now.getTime()) / 60_000)
}
