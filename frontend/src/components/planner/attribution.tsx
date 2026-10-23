import { cn } from '@/lib/utils'

/** Credits for the open data the planner runs on (ADR-0011). */
export function Attribution({ className }: { className?: string }) {
  return (
    <footer className={cn('text-xs text-muted-foreground', className)}>
      <p>
        Transit data:{' '}
        <a className="underline underline-offset-2" href="https://otd.delhi.gov.in" target="_blank" rel="noreferrer">
          Open Transit Data, Transport Dept., GNCTD
        </a>
        . Map and places: ©{' '}
        <a className="underline underline-offset-2" href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">
          OpenStreetMap
        </a>{' '}
        contributors.
      </p>
    </footer>
  )
}
