import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { AppShell } from '@/components/layout/app-shell'
import { json, mockApi } from '@/test/api-mock'
import { DESKTOP_QUERY } from '@/hooks/use-media-query'
import { setMediaQueries } from '@/test/media'

// jsdom has no WebGL, so the real map can't render here; Playwright covers it in a browser.
vi.mock('@/components/map/map-view', () => ({ default: () => <div data-testid="map" /> }))

async function chooseTrip(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByRole('combobox', { name: 'From' }), 'kashmere')
  // Arrow keys and Enter pick a suggestion, as in any combobox.
  await screen.findByRole('option', { name: /Kashmere Gate\s*Metro station/ })
  await user.keyboard('{Enter}')
  await user.type(screen.getByRole('combobox', { name: 'To' }), 'india gate')
  await user.click(await screen.findByRole('option', { name: /^India Gate\s*Bus stop/ }))
}

describe('planning a trip', () => {
  it('suggests places while typing, then lists options and shows directions', async () => {
    setMediaQueries({ [DESKTOP_QUERY]: true })
    const fetchMock = mockApi()
    const user = userEvent.setup()
    render(<AppShell />)

    await chooseTrip(user)

    const options = await screen.findByRole('list', { name: 'Route options' })
    const rows = within(options).getAllByRole('button')
    expect(rows.map((row) => row.textContent)).toEqual(
      expect.arrayContaining([expect.stringMatching(/^Auto\s*Fastest/)]),
    )
    // The trip collapsed into a summary that can be tapped to edit it.
    expect(screen.getByRole('button', { name: /Edit trip from Kashmere Gate to India Gate/ }))
      .toBeInTheDocument()

    await user.click(within(options).getByRole('button', { name: /^Bus 270/ }))
    await user.click(screen.getByRole('button', { name: 'Directions for Bus 270' }))

    const steps = screen.getByRole('list', { name: 'Steps' })
    expect(within(steps).getByText(/towards/)).toBeInTheDocument()
    expect(within(steps).getAllByText('270').length).toBeGreaterThan(0)

    const planCall = fetchMock.mock.calls.find(([url]) => String(url).endsWith('/trips/plan'))
    expect(JSON.parse(String(planCall?.[1]?.body))).toMatchObject({
      origin: { name: 'Kashmere Gate' },
      destination: { name: 'India Gate' },
      depart_at: null,
    })
  })

  it('works the same on phones, through the full-screen search', async () => {
    mockApi()
    const user = userEvent.setup()
    render(<AppShell />)

    await user.click(screen.getByRole('button', { name: 'From' }))
    await chooseTrip(user)

    // Both places chosen: the search screen gives way to the options under the map.
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    const options = await screen.findByRole('list', { name: 'Route options' })
    await user.click(within(options).getByRole('button', { name: /^Bus 270/ }))
    await user.click(screen.getByRole('button', { name: 'Directions for Bus 270' }))
    expect(screen.getByRole('list', { name: 'Steps' })).toHaveTextContent(/towards/)

    await user.click(screen.getByRole('button', { name: 'Back to all routes' }))
    await user.click(screen.getByRole('button', { name: 'Edit trip' }))
    expect(screen.getByRole('button', { name: 'From: Kashmere Gate' })).toBeInTheDocument()
  })

  it("says so when the route planner isn't available", async () => {
    setMediaQueries({ [DESKTOP_QUERY]: true })
    mockApi(() =>
      json({ detail: "The route planner isn't available right now. Please try again shortly." }, 503),
    )
    const user = userEvent.setup()
    render(<AppShell />)

    await chooseTrip(user)

    expect(await screen.findByRole('alert')).toHaveTextContent("route planner isn't available")
  })
})
