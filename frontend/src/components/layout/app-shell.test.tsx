import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { setMediaQueries } from '@/test/media'
import { AppShell } from './app-shell'

// jsdom has no WebGL, so the real map can't render here; Playwright covers it in a browser.
vi.mock('@/components/map/map-view', () => ({
  default: () => <div data-testid="map" />,
}))

describe('AppShell', () => {
  it('shows the planner as a side panel on laptops', async () => {
    setMediaQueries({ '(min-width: 1024px)': true })

    render(<AppShell />)

    const panel = screen.getByRole('complementary', { name: 'Trip planner' })
    expect(panel).toContainElement(screen.getByRole('heading', { name: 'Where to?' }))
    expect(await screen.findByTestId('map')).toBeInTheDocument()
  })

  it('shows the planner as a bottom sheet on phones', async () => {
    render(<AppShell />)

    expect(screen.queryByRole('complementary')).not.toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: 'Where to?' })).toBeInTheDocument()
  })

  it('expands the bottom sheet when a search field is focused', async () => {
    render(<AppShell />)
    const sheet = await screen.findByRole('dialog', { name: 'Trip planner' })
    const scrollArea = sheet.querySelector('.overflow-hidden')
    expect(scrollArea).not.toBeNull()

    await userEvent.click(screen.getByPlaceholderText(/^From/))

    // Only the fully expanded sheet scrolls (see PlannerSheet).
    expect(sheet.querySelector('.overflow-y-auto')).not.toBeNull()
  })
})
