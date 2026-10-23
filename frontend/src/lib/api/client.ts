import type { components } from './schema'

// Friendly names for the generated API types (`make api-types` regenerates schema.d.ts).
export type Place = components['schemas']['Place']
export type PlaceKind = Place['kind']
export type TripOption = components['schemas']['TripOption']
export type Leg = components['schemas']['Leg']
export type Fare = components['schemas']['Fare']
export type PlanRequest = components['schemas']['PlanRequest']
export type PlanResponse = components['schemas']['PlanResponse']

/** An error worth showing to the user, with a message written for them. */
export class ApiError extends Error {}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response
  try {
    response = await fetch(path, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init.headers },
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    throw new ApiError("Can't reach FlexTravel. Check your connection and try again.")
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    // The API's own messages (e.g. the 503 when the route planner is down) are user-facing.
    const detail = typeof body?.detail === 'string' ? body.detail : null
    throw new ApiError(detail ?? 'Something went wrong. Please try again.')
  }
  return response.json() as Promise<T>
}

export async function searchPlaces(query: string, signal?: AbortSignal): Promise<Place[]> {
  const params = new URLSearchParams({ q: query })
  const body = await request<{ places: Place[] }>(`/api/v1/places?${params}`, { signal })
  return body.places
}

export function planTrip(plan: PlanRequest, signal?: AbortSignal): Promise<PlanResponse> {
  return request('/api/v1/trips/plan', { method: 'POST', body: JSON.stringify(plan), signal })
}
