import type { ReactNode } from 'react'
import { Drawer } from 'vaul'
import { SHEET_SNAP_POINTS, type SheetSnapPoint } from './sheet-snap-points'

interface PlannerSheetProps {
  snapPoint: SheetSnapPoint
  onSnapPointChange: (snapPoint: SheetSnapPoint) => void
  children: ReactNode
}

/**
 * Mobile bottom sheet that is always present. Built directly on vaul rather than shadcn's
 * DrawerContent, because that one is a dismissible dialog with an overlay that would block
 * the map. Here: non-modal (the map stays usable), not dismissible, three snap heights.
 */
export function PlannerSheet({ snapPoint, onSnapPointChange, children }: PlannerSheetProps) {
  return (
    <Drawer.Root
      open
      modal={false}
      dismissible={false}
      snapPoints={[...SHEET_SNAP_POINTS]}
      activeSnapPoint={snapPoint}
      setActiveSnapPoint={(next) => next != null && onSnapPointChange(next as SheetSnapPoint)}
      noBodyStyles
    >
      <Drawer.Portal>
        <Drawer.Content
          aria-describedby={undefined}
          className="fixed inset-x-0 bottom-0 z-10 flex h-[94dvh] flex-col rounded-t-2xl border-t bg-background shadow-[0_-8px_30px_rgb(0_0_0/0.12)] outline-none"
        >
          <Drawer.Title className="sr-only">Trip planner</Drawer.Title>
          <Drawer.Handle className="mt-3 mb-1 !w-10 !bg-muted-foreground/30" />
          {/* Only the fully expanded sheet scrolls, so dragging the half sheet moves the sheet. */}
          <div
            className={
              snapPoint === SHEET_SNAP_POINTS[2] ? 'flex-1 overflow-y-auto' : 'flex-1 overflow-hidden'
            }
          >
            {children}
          </div>
        </Drawer.Content>
      </Drawer.Portal>
    </Drawer.Root>
  )
}
