import { BusFront, Landmark, LoaderCircle, MapPin, TrainFront, TramFront, X } from 'lucide-react'
import { type ReactNode, type Ref, useId, useState } from 'react'
import { createPortal } from 'react-dom'
import { usePlaceSearch } from '@/hooks/use-place-search'
import type { Place, PlaceKind } from '@/lib/api/client'
import { cn } from '@/lib/utils'

const KIND_ICONS: Record<PlaceKind, typeof MapPin> = {
  metro_station: TramFront,
  rail_station: TrainFront,
  bus_stop: BusFront,
  landmark: Landmark,
  address: MapPin,
}

interface PlaceFieldProps {
  label: string
  placeholder: string
  value: Place | null
  onChange: (place: Place | null) => void
  /** The dot or square drawn to the left, matching the map's start and end markers. */
  marker: ReactNode
  onFocus?: () => void
  inputRef?: Ref<HTMLInputElement>
  /**
   * Where the suggestions go. By default they drop down under the field; given an element
   * (the phone's search page), they fill it as a full-width list instead.
   */
  listContainer?: HTMLElement | null
}

/** Bold the part of `text` that matches what was typed, like ride apps do. */
function Highlight({ text, query }: { text: string; query: string }) {
  const at = text.toLowerCase().indexOf(query.trim().toLowerCase())
  if (!query.trim() || at < 0) return <>{text}</>
  const end = at + query.trim().length
  return (
    <>
      {text.slice(0, at)}
      <mark className="bg-transparent font-semibold text-foreground">{text.slice(at, end)}</mark>
      {text.slice(end)}
    </>
  )
}

/**
 * A search field with type-ahead suggestions, following the WAI-ARIA combobox pattern:
 * arrow keys move through suggestions, Enter picks one, Escape closes the list.
 *
 * The text starts from `value` and is then the field's own. When the place changes from
 * outside (swapping From and To), the parent remounts the field with a new `key`.
 */
export function PlaceField({
  label,
  placeholder,
  value,
  onChange,
  marker,
  onFocus,
  inputRef,
  listContainer,
}: PlaceFieldProps) {
  const id = useId()
  const listId = `${id}-suggestions`
  const [text, setText] = useState(value?.name ?? '')
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  // Search only while the text differs from the chosen place: after picking "Rajiv Chowk"
  // the field shows its name, which shouldn't trigger a new search.
  const query = open && text !== value?.name ? text : ''
  const search = usePlaceSearch(query)
  const places = search.places

  // The list can shrink while the highlight stays put; keep it on a real row.
  const activeIndex = Math.min(active, Math.max(places.length - 1, 0))

  function choose(place: Place) {
    onChange(place)
    setText(place.name)
    setOpen(false)
  }

  const showList = open && query.trim().length >= 2
  const busy = search.status === 'loading'
  // In the full-width list, rows are divided by lines and sized for thumbs.
  const fullWidth = Boolean(listContainer)

  const suggestions = (
    <>
      <ul
        id={listId}
        role="listbox"
        aria-label={`${label} suggestions`}
        className={fullWidth ? undefined : 'py-1'}
      >
        {places.map((place, index) => {
          const Icon = KIND_ICONS[place.kind]
          return (
            <li
              key={place.id}
              id={`${listId}-${index}`}
              role="option"
              aria-selected={index === activeIndex}
              // mousedown, not click: picking must happen before the input's blur.
              onMouseDown={(event) => {
                event.preventDefault()
                choose(place)
              }}
              onMouseMove={() => setActive(index)}
              className={cn(
                'flex cursor-pointer items-center gap-3',
                fullWidth ? 'gap-4 py-1' : 'px-3 py-2.5',
                index === activeIndex && (fullWidth ? 'bg-muted/60' : 'bg-muted'),
              )}
            >
              <span
                className={cn(
                  'grid shrink-0 place-items-center rounded-full bg-muted text-foreground in-aria-selected:bg-background',
                  fullWidth ? 'size-10' : 'size-9',
                )}
              >
                <Icon className="size-4" aria-hidden />
              </span>
              <span className={cn('min-w-0', fullWidth && 'flex-1 border-b py-2.5')}>
                <span
                  className={cn(
                    'block truncate text-foreground/80',
                    fullWidth ? 'text-base' : 'text-sm',
                  )}
                >
                  <Highlight text={place.name} query={query} />
                </span>
                {place.detail && (
                  <span className="block truncate text-xs text-muted-foreground">
                    {place.detail}
                  </span>
                )}
              </span>
            </li>
          )
        })}
      </ul>
      {search.status === 'done' && places.length === 0 && (
        <p className="px-4 py-3 text-sm text-muted-foreground">
          No places found. Try a station, stop or landmark name.
        </p>
      )}
      {search.status === 'error' && (
        <p role="alert" className="px-4 py-3 text-sm text-destructive">
          {search.message}
        </p>
      )}
      {busy && places.length === 0 && (
        <p className="px-4 py-3 text-sm text-muted-foreground">Searching…</p>
      )}
    </>
  )

  return (
    <div className="relative">
      <label htmlFor={id} className="sr-only">
        {label}
      </label>
      <span className="pointer-events-none absolute top-1/2 left-4 -translate-y-1/2">{marker}</span>
      <input
        id={id}
        role="combobox"
        aria-expanded={showList}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={
          showList && places[activeIndex] ? `${listId}-${activeIndex}` : undefined
        }
        ref={inputRef}
        autoComplete="off"
        spellCheck={false}
        placeholder={placeholder}
        value={text}
        onChange={(event) => {
          setText(event.target.value)
          setOpen(true)
          setActive(0)
          if (value) onChange(null) // typing over a chosen place un-chooses it
        }}
        onFocus={(event) => {
          event.target.select()
          setOpen(true)
          onFocus?.()
        }}
        onBlur={() => setOpen(false)}
        onKeyDown={(event) => {
          if (!showList || places.length === 0) return
          if (event.key === 'ArrowDown') {
            event.preventDefault()
            setActive((activeIndex + 1) % places.length)
          } else if (event.key === 'ArrowUp') {
            event.preventDefault()
            setActive((activeIndex - 1 + places.length) % places.length)
          } else if (event.key === 'Enter') {
            event.preventDefault()
            choose(places[activeIndex])
          } else if (event.key === 'Escape') {
            setOpen(false)
          }
        }}
        className="h-12 w-full rounded-lg bg-muted pr-10 pl-10 text-base font-medium outline-none placeholder:font-normal placeholder:text-muted-foreground focus:bg-background focus:ring-2 focus:ring-foreground"
      />
      {busy ? (
        <LoaderCircle
          className="absolute top-1/2 right-3 size-4 -translate-y-1/2 animate-spin text-muted-foreground"
          aria-hidden
        />
      ) : (
        text && (
          <button
            type="button"
            aria-label={`Clear ${label}`}
            onMouseDown={(event) => event.preventDefault()}
            onClick={() => {
              setText('')
              onChange(null)
            }}
            className="absolute top-1/2 right-2 grid size-7 -translate-y-1/2 place-items-center rounded-full text-muted-foreground hover:bg-background hover:text-foreground"
          >
            <X className="size-4" aria-hidden />
          </button>
        )
      )}

      {showList &&
        (listContainer ? (
          createPortal(<div className="pb-4">{suggestions}</div>, listContainer)
        ) : (
          <div className="absolute inset-x-0 top-full z-30 mt-2 overflow-hidden rounded-xl border bg-popover shadow-xl">
            {suggestions}
          </div>
        ))}
    </div>
  )
}
