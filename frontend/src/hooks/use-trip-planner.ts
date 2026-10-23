import { useEffect, useReducer } from 'react'
import { ApiError, type Place, type PlanResponse, planTrip, type TripOption } from '@/lib/api/client'

export type PlanStatus =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'ready'; response: PlanResponse }
  | { status: 'error'; message: string }

/** Which screen the planner shows: entering places, comparing options, or one option's steps. */
export type PlannerView = 'search' | 'options' | 'details'

export interface PlannerState {
  origin: Place | null
  destination: Place | null
  /** Delhi local time as `YYYY-MM-DDTHH:mm`, or null for "leave now". */
  departAt: string | null
  plan: PlanStatus
  selectedId: string | null
  view: PlannerView
  /** Bumped on every swap, so the From/To fields can reset their text (used as React keys). */
  swaps: number
}

type Action =
  | { type: 'setOrigin'; place: Place | null }
  | { type: 'setDestination'; place: Place | null }
  | { type: 'swap' }
  | { type: 'setDepartAt'; departAt: string | null }
  | { type: 'planStarted' }
  | { type: 'planDone'; response: PlanResponse }
  | { type: 'planFailed'; message: string }
  | { type: 'select'; id: string }
  | { type: 'showDetails' }
  | { type: 'showOptions' }
  | { type: 'back' }

export const initialState: PlannerState = {
  origin: null,
  destination: null,
  departAt: null,
  plan: { status: 'idle' },
  selectedId: null,
  view: 'search',
  swaps: 0,
}

/** New start or end. Without both, old results no longer apply, so they're cleared. */
function withPlaces(state: PlannerState, origin: Place | null, destination: Place | null) {
  const complete = origin !== null && destination !== null
  return {
    ...state,
    origin,
    destination,
    view: 'search' as const,
    plan: complete ? state.plan : { status: 'idle' as const },
    selectedId: complete ? state.selectedId : null,
  }
}

export function plannerReducer(state: PlannerState, action: Action): PlannerState {
  switch (action.type) {
    case 'setOrigin':
      return withPlaces(state, action.place, state.destination)
    case 'setDestination':
      return withPlaces(state, state.origin, action.place)
    case 'swap':
      return {
        ...state,
        origin: state.destination,
        destination: state.origin,
        swaps: state.swaps + 1,
      }
    case 'setDepartAt':
      return { ...state, departAt: action.departAt }
    case 'planStarted':
      return { ...state, plan: { status: 'loading' }, view: 'options' }
    case 'planDone':
      // Preselect the first option, as ride apps do, so the map shows a route right away.
      return {
        ...state,
        plan: { status: 'ready', response: action.response },
        selectedId: action.response.options[0]?.id ?? null,
      }
    case 'planFailed':
      return { ...state, plan: { status: 'error', message: action.message } }
    case 'select':
      return { ...state, selectedId: action.id }
    case 'showDetails':
      return state.selectedId ? { ...state, view: 'details' } : state
    case 'showOptions':
      return state.plan.status === 'idle' ? state : { ...state, view: 'options' }
    case 'back':
      return { ...state, view: state.view === 'details' ? 'options' : 'search' }
  }
}

/** `YYYY-MM-DDTHH:mm` in Delhi time -> an ISO time with Delhi's offset, for the API. */
function delhiIso(local: string): string {
  return `${local}:00+05:30`
}

export function useTripPlanner() {
  const [state, dispatch] = useReducer(plannerReducer, initialState)
  const { origin, destination, departAt } = state

  // Plan as soon as both places are chosen, and again whenever one of them or the time
  // changes. A newer search cancels the one still running.
  useEffect(() => {
    if (!origin || !destination) return
    const controller = new AbortController()
    dispatch({ type: 'planStarted' })
    planTrip(
      {
        origin: { name: origin.name, lat: origin.lat, lon: origin.lon },
        destination: { name: destination.name, lat: destination.lat, lon: destination.lon },
        depart_at: departAt ? delhiIso(departAt) : null,
      },
      controller.signal,
    ).then(
      (response) => dispatch({ type: 'planDone', response }),
      (error: unknown) => {
        if (controller.signal.aborted) return
        const message = error instanceof ApiError ? error.message : 'Something went wrong.'
        dispatch({ type: 'planFailed', message })
      },
    )
    return () => controller.abort()
  }, [origin, destination, departAt])

  const options = state.plan.status === 'ready' ? state.plan.response.options : []
  const selected: TripOption | null = options.find((o) => o.id === state.selectedId) ?? null

  return { state, dispatch, options, selected }
}

export type TripPlanner = ReturnType<typeof useTripPlanner>
