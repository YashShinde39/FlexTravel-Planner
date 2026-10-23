import { Route } from 'lucide-react'
import { cn } from '@/lib/utils'

export function Brand({ className }: { className?: string }) {
  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      <span className="grid size-8 place-items-center rounded-lg bg-primary text-primary-foreground">
        <Route className="size-4" aria-hidden />
      </span>
      <span className="font-heading text-base font-semibold tracking-tight">FlexTravel</span>
      <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">Delhi</span>
    </div>
  )
}
