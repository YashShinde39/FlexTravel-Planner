import { vi } from 'vitest'
import placesIndiaGate from './fixtures/places-india-gate.json'
import placesKashmere from './fixtures/places-kashmere.json'
import plan from './fixtures/plan-kashmere-gate-to-india-gate.json'

export const fixtures = { placesKashmere, placesIndiaGate, plan }

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

/**
 * Answers the app's API calls from the recorded fixtures. `planResponse` overrides the
 * trip plan reply, e.g. to simulate the route planner being down.
 */
export function mockApi(planResponse: () => Response = () => json(plan)) {
  return vi.spyOn(globalThis, 'fetch').mockImplementation(async (input: RequestInfo | URL) => {
    const url = new URL(String(input), 'http://localhost')
    if (url.pathname === '/api/v1/places') {
      const q = url.searchParams.get('q')?.toLowerCase() ?? ''
      if (q.startsWith('kash')) return json(placesKashmere)
      if (q.startsWith('india')) return json(placesIndiaGate)
      return json({ places: [] })
    }
    if (url.pathname === '/api/v1/trips/plan') return planResponse()
    return json({ detail: 'Not found' }, 404)
  })
}

export { json }
