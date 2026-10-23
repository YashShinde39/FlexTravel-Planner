import { describe, expect, it } from 'vitest'
import type { Place } from '@/lib/api/client'
import { fixtures } from '@/test/api-mock'
import { initialState, type PlannerState, plannerReducer } from './use-trip-planner'

const [kashmere] = fixtures.placesKashmere.places as Place[]
const [indiaGate] = fixtures.placesIndiaGate.places as Place[]

function ready(): PlannerState {
  const chosen = plannerReducer(
    plannerReducer(initialState, { type: 'setOrigin', place: kashmere }),
    { type: 'setDestination', place: indiaGate },
  )
  return plannerReducer(plannerReducer(chosen, { type: 'planStarted' }), {
    type: 'planDone',
    response: fixtures.plan as never,
  })
}

describe('plannerReducer', () => {
  it('preselects the first option when routes arrive', () => {
    const state = ready()
    expect(state.view).toBe('options')
    expect(state.selectedId).toBe(fixtures.plan.options[0].id)
  })

  it('swaps the places and bumps the swap counter', () => {
    const state = plannerReducer(ready(), { type: 'swap' })
    expect([state.origin?.name, state.destination?.name]).toEqual([indiaGate.name, kashmere.name])
    expect(state.swaps).toBe(1)
  })

  it('clears old routes when a place is removed', () => {
    const state = plannerReducer(ready(), { type: 'setDestination', place: null })
    expect(state.plan).toEqual({ status: 'idle' })
    expect(state.selectedId).toBeNull()
  })

  it('goes back from directions to the options, then to the form', () => {
    const details = plannerReducer(ready(), { type: 'showDetails' })
    expect(details.view).toBe('details')
    const options = plannerReducer(details, { type: 'back' })
    expect(options.view).toBe('options')
    expect(plannerReducer(options, { type: 'back' }).view).toBe('search')
  })
})
