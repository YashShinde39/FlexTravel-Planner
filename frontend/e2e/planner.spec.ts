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

test('plans a trip from suggestions to directions', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  page.on('console', (message) => message.type() === 'error' && errors.push(message.text()))
  await mockApi(page)
  await page.goto('/')

  await page.getByRole('combobox', { name: 'From' }).fill('kashmere')
  await page.getByRole('option', { name: /Kashmere Gate\s*Metro station/ }).click()
  await page.getByRole('combobox', { name: 'To' }).fill('india gate')
  await page.getByRole('option', { name: /^India Gate\s*Bus stop/ }).click()

  const options = page.getByRole('list', { name: 'Route options' })
  await expect(options.getByRole('button', { name: /^Auto\s*Fastest/ })).toBeVisible()
  await expect(options.getByRole('button', { name: /^Bus 270/ })).toBeAttached()

  // The first option is preselected; its directions are one tap away on any screen size.
  await page.getByRole('button', { name: /^Directions/ }).first().click()
  await expect(page.getByRole('list', { name: 'Steps' })).toContainText('India Gate')

  // The selected route is drawn on a real map.
  await expect(page.locator('canvas.maplibregl-canvas')).toBeVisible()
  await page.waitForTimeout(2000)
  expect(errors).toEqual([])
})

// The planner is a side panel where there's room beside the map and a bottom sheet on upright
// phones; either way it has to fit the screen it's on.
const SCREENS = [
  { name: 'a small phone', viewport: { width: 320, height: 568 }, panel: false },
  { name: 'a phone held sideways', viewport: { width: 844, height: 390 }, panel: true },
  { name: 'a tablet', viewport: { width: 768, height: 1024 }, panel: true },
  { name: 'a big monitor', viewport: { width: 2560, height: 1440 }, panel: true },
]

for (const screen of SCREENS) {
  test.describe(`on ${screen.name}`, () => {
    test.use({ viewport: screen.viewport })

    test('fits the planner on screen', async ({ page }) => {
      test.skip(test.info().project.name !== 'desktop', 'sets its own screen size')
      await mockApi(page)
      await page.goto('/')
      const { width, height } = screen.viewport
      // Polled, because the sheet slides into place.
      const within = (locator: ReturnType<Page['locator']>) =>
        expect
          .poll(async () => {
            const box = await locator.boundingBox()
            return box && box.x >= 0 && box.x + box.width <= width && box.y + box.height <= height
          })
          .toBe(true)

      await expect(page.getByRole('complementary', { name: 'Trip planner' })).toHaveCount(
        screen.panel ? 1 : 0,
      )
      // Both fields show without scrolling or dragging the sheet up.
      await within(page.getByRole('combobox', { name: 'From' }))
      await within(page.getByRole('combobox', { name: 'To' }))

      await page.getByRole('combobox', { name: 'From' }).fill('kashmere')
      await page.getByRole('option', { name: /Kashmere Gate\s*Metro station/ }).click()
      await page.getByRole('combobox', { name: 'To' }).fill('india gate')
      await page.getByRole('option', { name: /^India Gate\s*Bus stop/ }).click()

      // The chosen option's Directions button is reachable without scrolling.
      const directions = page.getByRole('button', { name: /^Directions/ }).first()
      await within(directions)
      expect(await page.evaluate('document.documentElement.scrollWidth')).toBe(width)
    })
  })
}
