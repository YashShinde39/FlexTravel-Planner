import { useCallback, useSyncExternalStore } from 'react'

/** Live result of a CSS media query, e.g. `useMediaQuery('(min-width: 768px)')`. */
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
 * Screens with room for the planner beside the map: tablets, laptops, and phones held
 * sideways (a bottom sheet would leave a sideways phone only a sliver of map).
 */
export const SIDE_PANEL_QUERY = '(min-width: 768px), (min-width: 560px) and (orientation: landscape)'

/** True: the planner is a side panel. False (phones held upright): a bottom sheet. */
export function useHasSidePanel(): boolean {
  return useMediaQuery(SIDE_PANEL_QUERY)
}
