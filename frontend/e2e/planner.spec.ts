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
