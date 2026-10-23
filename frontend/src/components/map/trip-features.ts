import type { FeatureCollection } from 'geojson'
import type { TripOption } from '@/lib/api/client'
import { lineColor } from '@/lib/modes'

/** The selected option as GeoJSON: one line per leg, plus the stops it boards and passes. */
export function tripFeatures(option: TripOption | null): FeatureCollection {
  if (!option) return { type: 'FeatureCollection', features: [] }
  return {
    type: 'FeatureCollection',
    features: option.legs.flatMap((leg) => {
      const line = {
        type: 'Feature' as const,
        // A Metro line is drawn in its colour; null falls back to the monochrome route.
        properties: { mode: leg.mode, color: lineColor(leg) ?? null },
        geometry: { type: 'LineString' as const, coordinates: leg.geometry },
      }
      if (leg.mode === 'walk' || !leg.route) return [line]
      const point = (stop: { lat: number; lon: number }, role: 'board' | 'pass') => ({
        type: 'Feature' as const,
        properties: { role },
        geometry: { type: 'Point' as const, coordinates: [stop.lon, stop.lat] },
      })
      return [
        line,
        ...leg.intermediate_stops.map((stop) => point(stop, 'pass')),
        point(leg.start, 'board'),
        point(leg.end, 'board'),
      ]
    }),
  }
}
