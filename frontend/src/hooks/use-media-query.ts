import { useCallback, useSyncExternalStore } from 'react'

/** Live result of a CSS media query, e.g. `useMediaQuery('(min-width: 1024px)')`. */
export function useMediaQuery(query: string): boolean {
  const subscribe = useCallback(
    (onChange: () => void) => {
      const list = window.matchMedia(query)
      list.addEventListener('change', onChange)
      return () => list.removeEventListener('change', onChange)
    },
    [query],
  )
  return useSyncExternalStore(subscribe, () => window.matchMedia(query).matches)
}

/**
 * How the planner is laid out, following Uber's web app:
 * - `desktop`: laptops and tablets held sideways. A top bar, then the planner in columns
 *   beside the map.
 * - `sideways`: phones held sideways. Planner and map side by side, without the top bar
 *   (Uber stacks them here, which leaves a sliver of map).
 * - `stacked`: phones and tablets held upright. The map on top, the planner below it.
 */
export type Layout = 'desktop' | 'sideways' | 'stacked'

export const DESKTOP_QUERY = '(min-width: 1024px) and (min-height: 500px)'
export const SIDEWAYS_QUERY = '(orientation: landscape) and (min-width: 560px)'
/** Desktops wide enough to keep the form, the options and the map side by side. */
export const WIDE_QUERY = '(min-width: 1280px)'

export function useLayout(): Layout {
  const desktop = useMediaQuery(DESKTOP_QUERY)
  const sideways = useMediaQuery(SIDEWAYS_QUERY)
  if (desktop) return 'desktop'
  return sideways ? 'sideways' : 'stacked'
}
