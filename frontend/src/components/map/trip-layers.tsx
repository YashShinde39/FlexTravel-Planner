import { useMemo } from 'react'
import { Layer, Marker, Source } from 'react-map-gl/maplibre'
import type { ColorScheme } from '@/hooks/use-color-scheme'
import type { Place, TripOption } from '@/lib/api/client'
import { tripFeatures } from './trip-features'

// Uber-style monochrome: the route in the text colour, outlined in the background colour.
// Metro lines keep their own colour, as on station maps.
const INK: Record<ColorScheme, string> = { light: '#000000', dark: '#ffffff' }
const PAPER: Record<ColorScheme, string> = { light: '#ffffff', dark: '#000000' }

const isRide = ['all', ['==', ['geometry-type'], 'LineString'], ['!=', ['get', 'mode'], 'walk']]

function EndpointMarker({ place, kind }: { place: Place; kind: 'origin' | 'destination' }) {
  return (
    <Marker longitude={place.lon} latitude={place.lat} anchor="center">
      <div className="relative" title={place.name}>
        <span
          className={`grid size-4 place-items-center bg-foreground shadow-sm ring-2 ring-background ${
            kind === 'origin' ? 'rounded-full' : 'rounded-[2px]'
          }`}
        >
          <span className={`size-1.5 bg-background ${kind === 'origin' ? 'rounded-full' : ''}`} />
        </span>
        <span className="absolute bottom-full left-1/2 mb-1.5 max-w-44 -translate-x-1/2 truncate rounded-md border bg-background/95 px-1.5 py-0.5 text-[0.6875rem] font-medium whitespace-nowrap text-foreground shadow-sm">
          {place.name}
        </span>
      </div>
    </Marker>
  )
}

interface TripLayersProps {
  colorScheme: ColorScheme
  origin: Place | null
  destination: Place | null
  option: TripOption | null
}

export function TripLayers({ colorScheme, origin, destination, option }: TripLayersProps) {
  const data = useMemo(() => tripFeatures(option), [option])
  const ink = INK[colorScheme]
  const paper = PAPER[colorScheme]

  return (
    <>
      <Source id="trip" type="geojson" data={data}>
        <Layer
          id="trip-casing"
          type="line"
          filter={isRide as never}
          layout={{ 'line-cap': 'round', 'line-join': 'round' }}
          paint={{ 'line-color': paper, 'line-width': 8 }}
        />
        <Layer
          id="trip-ride"
          type="line"
          filter={isRide as never}
          layout={{ 'line-cap': 'round', 'line-join': 'round' }}
          paint={{ 'line-color': ['coalesce', ['get', 'color'], ink], 'line-width': 4.5 }}
        />
        <Layer
          id="trip-walk"
          type="line"
          filter={['==', ['get', 'mode'], 'walk']}
          layout={{ 'line-cap': 'round', 'line-join': 'round' }}
          // Zero-length dashes with round caps draw as dots.
          paint={{ 'line-color': ink, 'line-width': 3, 'line-dasharray': [0, 2], 'line-opacity': 0.6 }}
        />
        <Layer
          id="trip-stops"
          type="circle"
          filter={['==', ['geometry-type'], 'Point']}
          // Stops passed are small ticks in the line's colour; where you get on and off is
          // marked more clearly.
          paint={{
            'circle-radius': ['match', ['get', 'role'], 'board', 4, 1.75],
            'circle-color': paper,
            'circle-stroke-color': ['coalesce', ['get', 'color'], ink],
            'circle-stroke-width': ['match', ['get', 'role'], 'board', 2, 1],
          }}
        />
      </Source>
      {origin && <EndpointMarker place={origin} kind="origin" />}
      {destination && <EndpointMarker place={destination} kind="destination" />}
    </>
  )
}
