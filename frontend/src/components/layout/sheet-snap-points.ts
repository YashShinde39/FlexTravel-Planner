/** Peek shows the heading and both fields; half shows results over the map; full is for typing. */
export type SheetSnap = 'peek' | 'half' | 'full'

export const SHEET_SNAPS: readonly SheetSnap[] = ['peek', 'half', 'full']

const PEEK_PX = 196
// Half the screen, but never less than the trip summary, the first option and its Directions
// button need, which is more than half of a small phone.
const HALF_FRACTION = 0.55
const HALF_MIN_PX = 380
// PlannerSheet leaves the rest (6%) below the screen out of its scrolling area.
const FULL_FRACTION = 0.94

/** How much of the screen the sheet covers at a snap point, in pixels. */
export function sheetHeightAt(snap: SheetSnap, windowHeight: number): number {
  switch (snap) {
    case 'peek':
      return PEEK_PX
    case 'half':
      return Math.round(Math.max(windowHeight * HALF_FRACTION, Math.min(HALF_MIN_PX, windowHeight * 0.8)))
    case 'full':
      return Math.round(windowHeight * FULL_FRACTION)
  }
}

/** The snap points in vaul's terms (pixels as '200px', or fractions of the screen). */
export function vaulSnapPoints(windowHeight: number): (string | number)[] {
  return SHEET_SNAPS.map((snap) =>
    snap === 'peek' ? `${PEEK_PX}px` : sheetHeightAt(snap, windowHeight) / windowHeight,
  )
}
