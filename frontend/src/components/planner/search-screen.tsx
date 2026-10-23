import { ArrowLeft } from 'lucide-react'
import { type Ref, useState } from 'react'
import type { TripPlanner } from '@/hooks/use-trip-planner'
import { TripForm } from './trip-form'

interface SearchScreenProps {
  planner: TripPlanner
  open: boolean
  onClose: () => void
  fromRef: Ref<HTMLInputElement>
  toRef: Ref<HTMLInputElement>
  onPlaceChosen: (field: 'from' | 'to') => void
}

/**
 * Phones: entering places takes the whole screen, as in Uber's "Plan your ride", so the
 * suggestions get the full width and the keyboard doesn't squeeze them under the map.
 *
 * Always rendered (hidden while closed), so a tap can open it and focus a field in one go:
 * phones only raise the keyboard for focus that happens during the tap itself.
 */
export function SearchScreen({
  planner,
  open,
  onClose,
  fromRef,
  toRef,
  onPlaceChosen,
}: SearchScreenProps) {
  // The element the suggestions are drawn into, below both fields.
  const [list, setList] = useState<HTMLElement | null>(null)
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="search-screen-title"
      hidden={!open}
      className="fixed inset-0 z-30 flex flex-col bg-background pt-[env(safe-area-inset-top)]"
    >
      <header className="grid grid-cols-[2.75rem_1fr_2.75rem] items-center px-2 py-2">
        <button
          type="button"
          onClick={onClose}
          aria-label="Back"
          className="grid size-11 place-items-center rounded-full hover:bg-muted"
        >
          <ArrowLeft className="size-6" aria-hidden />
        </button>
        <h2 id="search-screen-title" className="text-center text-lg font-bold">
          Plan your trip
        </h2>
      </header>
      <div className="mx-auto w-full max-w-2xl px-4 pt-2 pb-3">
        <TripForm
          planner={planner}
          listContainer={list}
          fromRef={fromRef}
          toRef={toRef}
          onPlaceChosen={onPlaceChosen}
        />
      </div>
      <div
        ref={setList}
        className="mx-auto min-h-0 w-full max-w-2xl flex-1 overflow-y-auto overscroll-contain px-4 pb-[env(safe-area-inset-bottom)]"
      />
    </div>
  )
}
