import { useSyncExternalStore } from 'react'

function subscribe(onChange: () => void) {
  window.addEventListener('resize', onChange)
  return () => window.removeEventListener('resize', onChange)
}

/** The viewport's height in pixels, updated on resize (e.g. a phone rotating). */
export function useWindowHeight(): number {
  return useSyncExternalStore(subscribe, () => window.innerHeight)
}
