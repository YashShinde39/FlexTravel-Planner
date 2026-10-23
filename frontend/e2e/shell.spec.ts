import { expect, test } from '@playwright/test'

test('planner and map load without errors', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  // Console errors count too: MapLibre reports a missing tile worker only via the console.
  page.on('console', (message) => message.type() === 'error' && errors.push(message.text()))

  await page.goto('/')

  await expect(page.getByRole('heading', { name: 'Where to?' })).toBeVisible()
  await expect(page.getByRole('combobox', { name: 'From' })).toBeVisible()
  await expect(page.locator('canvas.maplibregl-canvas')).toBeVisible()
  // Give the map time to fetch and decode its first tiles.
  await page.waitForTimeout(3000)
  expect(errors).toEqual([])
})

test.describe('in dark mode', () => {
  test.use({ colorScheme: 'dark' })

  test('follows the device setting', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('html')).toHaveClass(/\bdark\b/)
  })
})
