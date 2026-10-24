import {
  AdvancedMarker,
  APIProvider,
  ColorScheme,
  Map,
  Polyline,
  useMap,
} from '@vis.gl/react-google-maps'
import { Fragment, useEffect } from 'react'
import type { Place, TripOption } from '@/lib/api/client'
import { lineColor } from '@/lib/modes'
import { cn } from '@/lib/utils'
import { GOOGLE_MAPS } from './google-maps-config'
import type { MapViewProps } from './map-view'

const DELHI = { lat: 28.6139, lng: 77.209 }
// Keeps the camera where the planner has data (west, south, east, north as in map-view).
const NCR = { west: 76.6, south: 28.15, east: 77.8, north: 29.12 }
// Room around a fitted route, on top of the padding: up to 60px, less on a small map.
const FIT_MARGIN = 60
const FIT_MARGIN_SHARE = 0.12

const INK = { light: '#000000', dark: '#ffffff' }
const PAPER = { light: '#ffffff', dark: '#000000' }

/** Moves the camera to the selected route, or else to the chosen places. */
function FrameTrip({ padding, frameKey, origin, destination, option }: MapViewProps) {
  const map = useMap()
  useEffect(() => {
    if (!map) return
    const points = option
      ? option.legs.flatMap((leg) => leg.geometry.map(([lng, lat]) => ({ lat, lng })))
      : [origin, destination].filter((p) => p !== null).map((p) => ({ lat: p.lat, lng: p.lon }))
    if (points.length === 0) return
    if (points.length === 1) {
      map.panTo(points[0])
      map.setZoom(Math.max(map.getZoom() ?? 13, 13))
      return
    }
    const bounds = new google.maps.LatLngBounds()
    points.forEach((point) => bounds.extend(point))
    const div = map.getDiv()
    const margin = Math.min(
      FIT_MARGIN,
      Math.round(Math.min(div.clientWidth, div.clientHeight) * FIT_MARGIN_SHARE),
    )
    map.fitBounds(bounds, {
      top: (padding.top ?? 0) + margin,
      right: (padding.right ?? 0) + margin,
      bottom: (padding.bottom ?? 0) + margin,
      left: (padding.left ?? 0) + margin,
    })
    // Padding is listed by value: the object itself is new on every render.
  }, [map, option, origin, destination, padding.top, padding.right, padding.bottom, padding.left, frameKey])
  return null
}

/** The selected option's legs: rides in the line's colour (or ink) over a casing, walks as
 * dots. */
function RouteLines({ option, scheme }: { option: TripOption | null; scheme: 'light' | 'dark' }) {
  if (!option) return null
  return option.legs.map((leg, index) => {
    const path = leg.geometry.map(([lng, lat]) => ({ lat, lng }))
    if (leg.mode === 'walk') {
      const dot = {
        path: google.maps.SymbolPath.CIRCLE,
        fillColor: INK[scheme],
        fillOpacity: 0.6,
        strokeOpacity: 0,
        scale: 1.6,
      }
      return (
        <Polyline
          key={index}
          path={path}
          strokeOpacity={0}
          icons={[{ icon: dot, offset: '0', repeat: '7px' }]}
        />
      )
    }
    return (
      <Fragment key={index}>
        <Polyline path={path} strokeColor={PAPER[scheme]} strokeWeight={8} />
        <Polyline path={path} strokeColor={lineColor(leg) ?? INK[scheme]} strokeWeight={4.5} zIndex={1} />
      </Fragment>
    )
  })
}

function StopDot({ color, board }: { color: string; board: boolean }) {
  return (
    <span
      className="block rounded-full bg-background"
      style={{
        width: board ? 10 : 5,
        height: board ? 10 : 5,
        border: `${board ? 2 : 1}px solid ${color}`,
      }}
    />
  )
}

function EndpointMarker({ place, kind }: { place: Place; kind: 'origin' | 'destination' }) {
  return (
    // Anchored at the dot's centre (8px above the bottom), with the name tag above it.
    <AdvancedMarker
      position={{ lat: place.lat, lng: place.lon }}
      anchorLeft="-50%"
      anchorTop="calc(-100% + 8px)"
      zIndex={10}
    >
      <div className="flex flex-col items-center gap-1" title={place.name}>
        <span className="max-w-44 truncate rounded-md border bg-background/95 px-1.5 py-0.5 text-[0.6875rem] font-medium whitespace-nowrap text-foreground shadow-sm">
          {place.name}
        </span>
        <span
          className={cn(
            'grid size-4 place-items-center bg-foreground shadow-sm ring-2 ring-background',
            kind === 'origin' ? 'rounded-full' : 'rounded-[2px]',
          )}
        >
          <span className={cn('size-1.5 bg-background', kind === 'origin' && 'rounded-full')} />
        </span>
      </div>
    </AdvancedMarker>
  )
}

/**
 * The map on Google Maps (ADR-0017): the familiar map of Uber and Rome2rio, with the same
 * route drawing as the free map. Used when a Google Maps API key is configured.
 */
export default function GoogleMapView(props: MapViewProps) {
  const { colorScheme, showZoomButtons, origin, destination, option } = props
  const ink = INK[colorScheme]
  return (
    <APIProvider apiKey={GOOGLE_MAPS.apiKey} region="IN" language="en">
      <Map
        mapId={GOOGLE_MAPS.mapId}
        colorScheme={colorScheme === 'dark' ? ColorScheme.DARK : ColorScheme.LIGHT}
        defaultCenter={DELHI}
        defaultZoom={10.5}
        minZoom={9}
        restriction={{ latLngBounds: NCR, strictBounds: false }}
        gestureHandling="greedy"
        disableDefaultUI
        zoomControl={showZoomButtons}
        clickableIcons={false}
        style={{ position: 'absolute', inset: 0 }}
      >
        <FrameTrip {...props} />
        <RouteLines option={option} scheme={colorScheme} />
        {option?.legs.flatMap((leg, legIndex) => {
          if (leg.mode === 'walk' || !leg.route) return []
          const color = lineColor(leg) ?? ink
          const stops = [
            ...leg.intermediate_stops.map((stop) => ({ stop, board: false })),
            { stop: leg.start, board: true },
            { stop: leg.end, board: true },
          ]
          return stops.map(({ stop, board }, index) => (
            <AdvancedMarker
              key={`${legIndex}-${index}`}
              position={{ lat: stop.lat, lng: stop.lon }}
              anchorLeft="-50%"
              anchorTop="-50%"
              zIndex={board ? 2 : 1}
            >
              <StopDot color={color} board={board} />
            </AdvancedMarker>
          ))
        })}
        {origin && <EndpointMarker place={origin} kind="origin" />}
        {destination && <EndpointMarker place={destination} kind="destination" />}
      </Map>
    </APIProvider>
  )
}
