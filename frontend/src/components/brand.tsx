import { Route } from 'lucide-react'
import { cn } from '@/lib/utils'

export function Brand({ className }: { className?: string }) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <span className="grid size-7 place-items-center rounded-md bg-primary text-primary-foreground">
        <Route className="size-4" strokeWidth={2.25} aria-hidden />
      </span>
      <span className="font-heading text-[0.9375rem] font-semibold tracking-tight">FlexTravel</span>
      <span className="text-[0.8125rem] text-muted-foreground">Delhi NCR</span>
    </div>
  )
}
