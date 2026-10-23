import { useEffect } from 'react'
import { useMediaQuery } from './use-media-query'

export type ColorScheme = 'light' | 'dark'

/**
 * Follows the device's light/dark setting and keeps the `dark` class on <html> in sync,
 * which switches the shadcn/ui theme. index.html sets the initial class before first paint.
 */
export function useColorScheme(): ColorScheme {
  const scheme: ColorScheme = useMediaQuery('(prefers-color-scheme: dark)') ? 'dark' : 'light'

  useEffect(() => {
    document.documentElement.classList.toggle('dark', scheme === 'dark')
  }, [scheme])

  return scheme
}
