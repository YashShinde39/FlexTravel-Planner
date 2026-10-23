import { describe, expect, it } from 'vitest'
import { formatDistance, formatDuration, formatFare, formatTime } from './format'

describe('format', () => {
  it('shows times in Delhi time, with ~ for estimates', () => {
    expect(formatTime('2026-10-24T03:34:00Z')).toBe('09:04')
    expect(formatTime('2026-10-24T09:04:00+05:30', true)).toBe('~09:04')
  })

  it.each([
    [30, '1 min'],
    [44 * 60, '44 min'],
    [65 * 60, '1 h 5 min'],
    [120 * 60, '2 h'],
  ])('formats %i seconds as %s', (seconds, text) => {
    expect(formatDuration(seconds)).toBe(text)
  })

  it.each([
    [354, '350 m'],
    [1234, '1.2 km'],
    [12_400, '12 km'],
  ])('formats %i metres as %s', (metres, text) => {
    expect(formatDistance(metres)).toBe(text)
  })

  it('shows a single fare or a range', () => {
    expect(formatFare({ min: 104, max: 104, currency: 'INR' })).toBe('₹104')
    expect(formatFare({ min: 10, max: 20, currency: 'INR' })).toBe('₹10–20')
  })
})
