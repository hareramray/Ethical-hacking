import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-logic').click()
})

async function compare(page, scenario) {
  await page.getByTestId('logic-scenario').selectOption(scenario)
  await page.getByTestId('logic-run').click()
  await expect(page.getByTestId('logic-summary')).toBeVisible()
  return { vulnerable: page.getByTestId('logic-vulnerable-result'), fixed: page.getByTestId('logic-fixed-result') }
}

test('Logic: a legitimate redemption credits ten points in both handlers', async ({ page }) => {
  const results = await compare(page, 'single')
  for (const result of Object.values(results)) {
    await expect(result.getByTestId('logic-redemptions')).toHaveText('1')
    await expect(result.getByTestId('logic-points')).toHaveText('10')
    await expect(result.getByTestId('logic-attempts').locator('pre')).toHaveCount(1)
    await expect(result.getByTestId('logic-attempts')).toContainText('redeemed (+10 points)')
  }
})

test('Logic: sequential replay looks safe for both handlers', async ({ page }) => {
  const results = await compare(page, 'sequential')
  for (const result of Object.values(results)) {
    await expect(result.getByTestId('logic-redemptions')).toHaveText('1')
    await expect(result.getByTestId('logic-points')).toHaveText('10')
    await expect(result.getByTestId('logic-attempts')).toContainText('Attempt 2: already_used (+0 points)')
  }
})

test('Logic: forced overlap exposes duplicate credits and each run starts fresh', async ({ page }) => {
  let results = await compare(page, 'concurrent')
  await expect(page.getByTestId('logic-summary')).toContainText('forced overlap')
  await expect(results.vulnerable.getByTestId('logic-redemptions')).toHaveText('2')
  await expect(results.vulnerable.getByTestId('logic-points')).toHaveText('20')
  await expect(results.fixed.getByTestId('logic-redemptions')).toHaveText('1')
  await expect(results.fixed.getByTestId('logic-points')).toHaveText('10')
  await expect(results.fixed.getByTestId('logic-attempts')).toContainText('already_used (+0 points)')
  await page.getByTestId('logic-scenario').selectOption('single')
  await expect(page.getByTestId('logic-summary')).toHaveCount(0)
  await expect(results.vulnerable.getByTestId('logic-points')).toHaveCount(0)
  results = await compare(page, 'single')
  await expect(results.vulnerable.getByTestId('logic-redemptions')).toHaveText('1')
  await expect(results.fixed.getByTestId('logic-redemptions')).toHaveText('1')
})
