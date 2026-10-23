import { describe, expect, it } from 'vitest'
import { sheetHeightAt, vaulSnapPoints } from './sheet-snap-points'

describe('sheet heights', () => {
  it('opens to half of a typical phone', () => {
    expect(sheetHeightAt('half', 852)).toBe(469)
  })

  it('opens further on small phones, so the first option and its button fit', () => {
    expect(sheetHeightAt('half', 568)).toBe(380)
  })

  it('gives vaul the same heights as fractions of the screen', () => {
    expect(vaulSnapPoints(568)).toEqual(['196px', 380 / 568, 534 / 568])
  })
})
