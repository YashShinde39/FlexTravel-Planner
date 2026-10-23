import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { DESKTOP_QUERY, SIDEWAYS_QUERY, WIDE_QUERY } from '@/hooks/use-media-query'
import { setMediaQueries } from '@/test/media'
import { AppShell } from './app-shell'

// jsdom has no WebGL, so the real map can't render here; Playwright covers it in a browser.
vi.mock('@/components/map/map-view', () => ({
  default: () => <div data-testid="map" />,
}))

describe('AppShell', () => {
  it('has a top bar and the form beside the map on laptops', async () => {
    setMediaQueries({ [DESKTOP_QUERY]: true, [WIDE_QUERY]: true })
    render(<AppShell />)

    expect(screen.getByRole('banner')).toHaveTextContent('FlexTravel')
    const planner = screen.getByRole('complementary', { name: 'Trip planner' })
    expect(planner).toContainElement(screen.getByRole('combobox', { name: 'From' }))
    expect(await screen.findByTestId('map')).toBeInTheDocument()
  })

  it('puts the planner beside the map without a top bar on sideways phones', () => {
    setMediaQueries({ [SIDEWAYS_QUERY]: true })
    render(<AppShell />)

    expect(screen.queryByRole('banner')).not.toBeInTheDocument()
    expect(screen.getByRole('complementary', { name: 'Trip planner' })).toBeInTheDocument()
  })

  it('stacks the map above the planner on upright phones', () => {
    render(<AppShell />)

    expect(screen.queryByRole('complementary')).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Where to?' })).toBeInTheDocument()
    // The fields open a full-screen search; until then they are buttons.
    expect(screen.getByRole('button', { name: 'From' })).toBeInTheDocument()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('opens the full-screen search with the tapped field focused', async () => {
    render(<AppShell />)

    await userEvent.click(screen.getByRole('button', { name: 'To' }))

    expect(screen.getByRole('dialog', { name: 'Plan your trip' })).toBeVisible()
    expect(screen.getByRole('combobox', { name: 'To' })).toHaveFocus()
    await userEvent.click(screen.getByRole('button', { name: 'Back' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
