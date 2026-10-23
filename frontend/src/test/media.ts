import { vi } from 'vitest'

/**
 * jsdom has no matchMedia. This stub answers queries from a table that tests set, e.g.
 * `setMediaQueries({ [DESKTOP_QUERY]: true })`; unlisted queries don't match.
 */
let matches: Record<string, boolean> = {}

export function setMediaQueries(table: Record<string, boolean>) {
  matches = table
}

vi.stubGlobal('matchMedia', (query: string) => ({
  matches: matches[query] ?? false,
  media: query,
  onchange: null,
  addEventListener: () => {},
  removeEventListener: () => {},
  addListener: () => {},
  removeListener: () => {},
  dispatchEvent: () => false,
}))
