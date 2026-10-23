import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { PlanResponse } from '@/lib/api/client'
import metroPlan from '@/test/fixtures/plan-samaypur-badli-to-noida-city-centre.json'
import { OptionList } from './option-list'
import { TripDetails } from './trip-details'

// A real response: Samaypur Badli to Noida City Centre, Yellow Line then Blue Line.
const plan = metroPlan as unknown as PlanResponse
const metro = plan.options.find((o) => o.title === 'Yellow Line + Blue Line')!

describe('a Metro trip', () => {
  it('shows each line as a badge in its own colour', () => {
    render(<OptionList options={plan.options} selectedId={metro.id} onSelect={() => {}} />)

    const row = screen.getByRole('button', { name: /^Yellow Line \+ Blue Line/ })
    const yellow = within(row).getByText('Yellow Line', { selector: 'span' })
    expect(yellow).toHaveStyle({ backgroundColor: '#FFDF00', color: '#000000' })
    expect(within(row).getByText('Blue Line', { selector: 'span' })).toHaveStyle({
      backgroundColor: '#4169E1',
    })
  })

  it('describes the walk between lines as a change, priced as one Metro journey', () => {
    render(<TripDetails option={metro} />)

    const steps = screen.getByRole('list', { name: 'Steps' })
    expect(within(steps).getByText(/^Into the station · \d+ min$/)).toBeInTheDocument()
    expect(within(steps).getByText(/^Change to the Blue Line · \d+ min$/)).toBeInTheDocument()
    expect(screen.getByText(/smart cards save 10%/)).toBeInTheDocument()
    expect(metro.fare).toMatchObject({ min: 64, max: 64 })
  })
})
