import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-webhook').click()
})

async function compare(page, fixture) {
  await page.getByTestId('webhook-fixture').selectOption(fixture)
  await page.getByTestId('webhook-run').click()
  const vulnerable = page.getByTestId('webhook-vulnerable-result')
  const fixed = page.getByTestId('webhook-fixed-result')
  await expect(vulnerable.getByTestId('webhook-balance')).toBeVisible()
  await expect(fixed.getByTestId('webhook-balance')).toBeVisible()
  await expect(page.getByTestId('webhook-run')).toBeEnabled()
  return { vulnerable, fixed }
}

test('Webhooks: valid distinct events still credit the ledger and each run resets', async ({ page }) => {
  let results = await compare(page, 'distinct-events')
  for (const result of Object.values(results)) {
    await expect(result.getByTestId('webhook-balance')).toHaveText('20')
    await expect(result.getByTestId('webhook-delivery-outcome')).toHaveText(['applied', 'applied'])
  }
  await expect(results.fixed.getByTestId('webhook-recorded-ids')).toHaveText('evt_demo_1, evt_demo_2')
  await page.getByTestId('webhook-fixture').selectOption('normal')
  await expect(results.fixed.getByTestId('webhook-balance')).toHaveCount(0)
  results = await compare(page, 'normal')
  for (const result of Object.values(results)) await expect(result.getByTestId('webhook-balance')).toHaveText('10')
})

test('Webhooks: signature checking rejects altered bytes while both handlers validate schema', async ({ page }) => {
  let results = await compare(page, 'body-tampered')
  for (const result of Object.values(results)) {
    await expect(result.getByTestId('webhook-balance')).toHaveText('0')
    await expect(result.getByTestId('webhook-delivery-outcome')).toHaveText('rejected')
    await expect(result.getByTestId('webhook-signature-valid')).toHaveText('No')
    await result.locator('summary').click()
    await expect(result.getByTestId('webhook-body')).toContainText('"units":20')
    await expect(result.getByTestId('webhook-body').locator('*')).toHaveCount(0)
  }
  results = await compare(page, 'invalid-schema')
  for (const result of Object.values(results)) {
    await expect(result.getByTestId('webhook-balance')).toHaveText('0')
    await expect(result.getByTestId('webhook-signature-valid')).toHaveText('Yes')
    await expect(result.getByTestId('webhook-delivery-outcome')).toHaveText('rejected')
  }
})

test('Webhooks: old and future signed deliveries need freshness checks', async ({ page }) => {
  for (const fixture of ['stale', 'future']) {
    const results = await compare(page, fixture)
    await expect(results.vulnerable.getByTestId('webhook-balance')).toHaveText('10')
    await expect(results.fixed.getByTestId('webhook-balance')).toHaveText('0')
    await expect(results.fixed.getByTestId('webhook-signature-valid')).toHaveText('Yes')
    await expect(results.fixed.getByTestId('webhook-recorded-ids')).toHaveText('None')
    await expect(results.fixed).toContainText('outside the 300-second past/future allowance')
  }
})

test('Webhooks: identical replay and a freshly signed retry apply only once', async ({ page }) => {
  for (const fixture of ['duplicate', 'resigned-retry']) {
    const results = await compare(page, fixture)
    await expect(results.vulnerable.getByTestId('webhook-balance')).toHaveText('20')
    await expect(results.fixed.getByTestId('webhook-balance')).toHaveText('10')
    await expect(results.fixed.getByTestId('webhook-delivery-outcome')).toHaveText(['applied', 'duplicate'])
    await expect(results.fixed.getByTestId('webhook-signature-valid')).toHaveText(['Yes', 'Yes'])
    await expect(results.fixed.getByTestId('webhook-balance-change').nth(1)).toHaveText('10 → 10 (0 points)')
    const signatures = await results.fixed.getByTestId('webhook-signature').allTextContents()
    expect(signatures[0] === signatures[1]).toBe(fixture === 'duplicate')
    await expect(results.fixed.getByTestId('webhook-recorded-ids')).toHaveText('evt_demo_1')
  }
})
