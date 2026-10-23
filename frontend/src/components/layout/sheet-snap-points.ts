/** Peek shows the heading and first field; half shows results over the map; full is for typing. */
export const SHEET_SNAP_POINTS = ['216px', 0.55, 0.94] as const
export type SheetSnapPoint = (typeof SHEET_SNAP_POINTS)[number]

/** Height of the peeking sheet, which the map leaves clear when centring. */
export const SHEET_PEEK_PX = 216
