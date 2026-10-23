import { readFileSync } from 'node:fs'
import { expect, type Page, test } from '@playwright/test'

// The recorded API responses the unit tests use too, so this runs without a backend.
const fixture = (name: string) =>
  readFileSync(new URL(`../src/test/fixtures/${name}.json`, import.meta.url), 'utf8')

async function mockApi(page: Page) {
  await page.route('**/api/v1/places?*', (route) => {
    const q = new URL(route.request().url()).searchParams.get('q')?.toLowerCase() ?? ''
    const name = q.startsWith('kash') ? 'places-kashmere' : 'places-india-gate'
    return route.fulfill({ contentType: 'application/json', body: fixture(name) })
  })
  await page.route('**/api/v1/trips/plan', (route) =>
    route.fulfill({
      contentType: 'application/json',
      body: fixture('plan-kashmere-gate-to-india-gate'),
    }),
  )
}

async function chooseTrip(page: Page) {
  // On phones the fields are buttons that open a full-screen search.
  const fromButton = page.getByRole('button', { name: 'From', exact: true })
  if (await fromButton.isVisible()) await fromButton.click()
  await page.getByRole('combobox', { name: 'From' }).fill('kashmere')
  await page.getByRole('option', { name: /Kashmere Gate\s*Metro station/ }).click()
  await page.getByRole('combobox', { name: 'To' }).fill('india gate')
  await page.getByRole('option', { name: /^India Gate\s*Bus stop/ }).click()
}

test('plans a trip from suggestions to directions', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  page.on('console', (message) => message.type() === 'error' && errors.push(message.text()))
  await mockApi(page)
  await page.goto('/')

  await chooseTrip(page)

  const options = page.getByRole('list', { name: 'Route options' })
  await expect(options.getByRole('button', { name: /^Auto\s*Fastest/ })).toBeVisible()
  await expect(options.getByRole('button', { name: /^Bus 270/ })).toBeAttached()

  // The first option is preselected; its directions are one tap away on any screen size.
  await page.getByRole('button', { name: /^Directions for/ }).click()
  await expect(page.getByRole('list', { name: 'Steps' })).toContainText('India Gate')

  // The selected route is drawn on a real map.
  await expect(page.locator('canvas.maplibregl-canvas')).toBeVisible()
  await page.waitForTimeout(2000)
  expect(errors).toEqual([])
})

// Like Uber's site, the planner is laid out per device: a top bar and columns on laptops,
// the map above a panel on phones and upright tablets, side by side on sideways phones.
const SCREENS = [
  { name: 'a small phone', viewport: { width: 320, height: 568 }, layout: 'stacked' },
  { name: 'an upright tablet', viewport: { width: 768, height: 1024 }, layout: 'stacked' },
  { name: 'a phone held sideways', viewport: { width: 844, height: 390 }, layout: 'sideways' },
  { name: 'a small laptop', viewport: { width: 1024, height: 768 }, layout: 'desktop' },
  { name: 'a big monitor', viewport: { width: 2560, height: 1440 }, layout: 'desktop' },
] as const

for (const screen of SCREENS) {
  test.describe(`on ${screen.name}`, () => {
    test.use({ viewport: screen.viewport })

    test('fits the planner and the map on screen', async ({ page }) => {
      test.skip(test.info().project.name !== 'desktop', 'sets its own screen size')
      await mockApi(page)
      await page.goto('/')
      const { width, height } = screen.viewport
      // Polled, because the map and panels settle into place.
      const within = (locator: ReturnType<Page['locator']>) =>
        expect
          .poll(async () => {
            const box = await locator.boundingBox()
            return box && box.x >= 0 && box.x + box.width <= width && box.y + box.height <= height
          })
          .toBe(true)

      await expect(page.getByRole('banner')).toHaveCount(screen.layout === 'desktop' ? 1 : 0)
      await within(page.getByRole(screen.layout === 'stacked' ? 'button' : 'combobox', { name: 'To', exact: true }))

      await chooseTrip(page)

      // The chosen option's Directions button is reachable without scrolling, and the route
      // has a real share of the screen.
      await within(page.getByRole('button', { name: /^Directions for/ }))
      const map = await page.locator('canvas.maplibregl-canvas').boundingBox()
      expect(map!.width * map!.height).toBeGreaterThan(width * height * 0.3)
      expect(await page.evaluate('document.documentElement.scrollWidth')).toBe(width)
    })
  })
}
