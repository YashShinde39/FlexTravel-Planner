import { useEffect, useState } from 'react'
import { ApiError, type Place, searchPlaces } from '@/lib/api/client'

const DEBOUNCE_MS = 200
const MIN_LENGTH = 2

type SearchState =
  | { status: 'idle'; places: Place[] }
  | { status: 'loading'; places: Place[] } // keeps the previous list while typing
  | { status: 'done'; places: Place[] }
  | { status: 'error'; places: Place[]; message: string }

interface Result {
  query: string
  places: Place[]
  error?: string
}

/**
 * Suggestions for what's typed, fetched after a short pause in typing. Each new query
 * cancels the request before it, so a slow early response can't overwrite a newer one.
 */
export function usePlaceSearch(query: string): SearchState {
  const [result, setResult] = useState<Result | null>(null)
  const trimmed = query.trim()
  const searchable = trimmed.length >= MIN_LENGTH

  useEffect(() => {
    if (!searchable) return
    const controller = new AbortController()
    const timer = setTimeout(() => {
      searchPlaces(trimmed, controller.signal).then(
        (places) => setResult({ query: trimmed, places }),
        (error: unknown) => {
          if (controller.signal.aborted) return
          const message = error instanceof ApiError ? error.message : 'Search failed.'
          setResult({ query: trimmed, places: [], error: message })
        },
      )
    }, DEBOUNCE_MS)
    return () => {
      clearTimeout(timer)
      controller.abort()
    }
  }, [trimmed, searchable])

  // Derived from the latest result rather than stored, so it can never go stale.
  if (!searchable) return { status: 'idle', places: [] }
  if (result?.query !== trimmed) return { status: 'loading', places: result?.places ?? [] }
  if (result.error) return { status: 'error', places: [], message: result.error }
  return { status: 'done', places: result.places }
}
