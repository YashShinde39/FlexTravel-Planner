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

/** Laptop and larger: the planner is a side panel. Smaller: a bottom sheet. */
export function useIsDesktop(): boolean {
  return useMediaQuery('(min-width: 1024px)')
}
