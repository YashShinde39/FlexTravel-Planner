import { type ReactNode, useMemo } from 'react'
import { Drawer } from 'vaul'
import { useWindowHeight } from '@/hooks/use-window-size'
import { SHEET_SNAPS, type SheetSnap, vaulSnapPoints } from './sheet-snap-points'

interface PlannerSheetProps {
  snap: SheetSnap
  onSnapChange: (snap: SheetSnap) => void
  children: ReactNode
}

/**
 * Mobile bottom sheet that is always present. Built directly on vaul rather than shadcn's
 * DrawerContent, because that one is a dismissible dialog with an overlay that would block
 * the map. Here: non-modal (the map stays usable), not dismissible, three snap heights.
 */
export function PlannerSheet({ snap, onSnapChange, children }: PlannerSheetProps) {
  // Recomputed only when the screen's height changes, e.g. a phone rotating.
  const windowHeight = useWindowHeight()
  const snapPoints = useMemo(() => vaulSnapPoints(windowHeight), [windowHeight])
  return (
    <Drawer.Root
      open
      modal={false}
      dismissible={false}
      snapPoints={snapPoints}
      activeSnapPoint={snapPoints[SHEET_SNAPS.indexOf(snap)]}
      setActiveSnapPoint={(next) => {
        const index = snapPoints.indexOf(next ?? -1)
        if (index !== -1) onSnapChange(SHEET_SNAPS[index])
      }}
      noBodyStyles
    >
      <Drawer.Portal>
        {/*
          Full screen height: vaul places each snap point as if the sheet were the screen's
          height, so a shorter sheet would sit lower than every snap point says.
        */}
        <Drawer.Content
          aria-describedby={undefined}
          className="fixed inset-x-0 bottom-0 z-10 flex h-dvh flex-col rounded-t-2xl border-t bg-background shadow-[0_-8px_30px_rgb(0_0_0/0.12)] outline-none"
        >
          <Drawer.Title className="sr-only">Trip planner</Drawer.Title>
          <Drawer.Handle className="mt-3 mb-1 !w-10 !bg-muted-foreground/30" />
          {/*
            Only the fully expanded sheet scrolls, so dragging the half sheet moves the sheet.
            Expanded, the sheet's bottom 6% is below the screen (it opens to 94%), so the
            scrolling area stops short of it.
          */}
          <div
            className={
              snap === 'full'
                ? 'flex-1 overflow-y-auto overscroll-contain mb-[6dvh]'
                : 'flex-1 overflow-hidden'
            }
          >
            {children}
          </div>
        </Drawer.Content>
      </Drawer.Portal>
    </Drawer.Root>
  )
}
