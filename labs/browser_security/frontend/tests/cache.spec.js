import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-cache').click()
})

async function compare(page, fixture) {
  await page.getByTestId('cache-fixture').selectOption(fixture)
  await page.getByTestId('cache-run').click()
  const vulnerable = page.getByTestId('cache-vulnerable-result')
  const fixed = page.getByTestId('cache-fixed-result')
  await expect(vulnerable.getByTestId('cache-request-2')).toBeVisible()
  await expect(fixed.getByTestId('cache-request-2')).toBeVisible()
  await expect(page.getByTestId('cache-run')).toBeEnabled()
  return { vulnerable, fixed }
}

test('cache: ordinary private responses work while the fixed path stores no private data', async ({ page }) => {
  const { vulnerable, fixed } = await compare(page, 'private-control')
  for (const result of [vulnerable, fixed]) {
    await expect(result.locator('.traversal-outcome')).toHaveText('no disclosure')
    await expect(result.getByTestId('cache-request-1').getByTestId('cache-marker')).toHaveText('PRIVATE_ADA_BLUE')
    await expect(result.getByTestId('cache-request-2').getByTestId('cache-marker')).toHaveText('PRIVATE_ADA_BLUE')
  }
  await expect(vulnerable.getByTestId('cache-request-2').getByTestId('cache-decision')).toHaveText('HIT')
  await expect(vulnerable.getByTestId('cache-origin-reads')).toHaveText('1')
  await expect(vulnerable.getByTestId('cache-entries')).toContainText('PRIVATE_ADA_BLUE')
  await expect(fixed.getByTestId('cache-request-2').getByTestId('cache-decision')).toHaveText('BYPASS')
  await expect(fixed.getByTestId('cache-origin-reads')).toHaveText('2')
  await expect(fixed.getByTestId('cache-lookups')).toHaveText('0')
  await expect(fixed.getByTestId('cache-writes')).toHaveText('0')
  await expect(fixed.getByTestId('cache-entries')).toHaveText('[]')
})

test('cache: user and tenant boundaries preserve each requester own private marker', async ({ page }) => {
  for (const [fixture, expected] of [['cross-user', 'PRIVATE_BEA_BLUE'], ['cross-tenant', 'PRIVATE_CY_AMBER']]) {
    const { vulnerable, fixed } = await compare(page, fixture)
    await expect(vulnerable.locator('.traversal-outcome')).toHaveText('exposed')
    await expect(vulnerable.getByTestId('cache-request-2').getByTestId('cache-marker')).toHaveText('PRIVATE_ADA_BLUE')
    await expect(vulnerable.getByTestId('cache-request-2').getByTestId('cache-authorization')).toHaveText('skipped on cache hit')
    await expect(fixed.getByTestId('cache-request-2').getByTestId('cache-marker')).toHaveText(expected)
    await expect(fixed.getByTestId('cache-request-2').getByTestId('cache-authorization')).toHaveText('allowed')
    await expect(fixed.locator('.traversal-outcome')).toHaveText('no disclosure')
    await expect(fixed.getByTestId('cache-entries')).toHaveText('[]')
  }
})

test('cache: revoked and anonymous requests cannot consume fixed private responses', async ({ page }) => {
  for (const fixture of ['revoked', 'logout']) {
    const { vulnerable, fixed } = await compare(page, fixture)
    await expect(vulnerable.getByTestId('cache-request-2').getByTestId('cache-marker')).toHaveText('PRIVATE_ADA_BLUE')
    await expect(vulnerable.locator('.traversal-outcome')).toHaveText('exposed')
    const denied = fixed.getByTestId('cache-request-2')
    await expect(denied.getByTestId('cache-status')).toHaveText('403')
    await expect(denied.getByTestId('cache-decision')).toHaveText('NOT_CHECKED')
    await expect(denied.getByTestId('cache-marker')).toHaveText('No content returned')
    await expect(fixed.getByTestId('cache-origin-reads')).toHaveText('1')
    await expect(fixed.getByTestId('cache-lookups')).toHaveText('0')
  }
})

test('cache: public HIT is preserved and selecting a new fixture discards old evidence', async ({ page }) => {
  const results = await compare(page, 'public-control')
  for (const result of Object.values(results)) {
    await expect(result.getByTestId('cache-request-1').getByTestId('cache-decision')).toHaveText('MISS')
    await expect(result.getByTestId('cache-request-2').getByTestId('cache-decision')).toHaveText('HIT')
    await expect(result.getByTestId('cache-request-2').getByTestId('cache-marker')).toHaveText('PUBLIC_CATALOG')
    await expect(result.getByTestId('cache-origin-reads')).toHaveText('1')
    await expect(result.getByTestId('cache-writes')).toHaveText('1')
  }
  await expect(results.fixed.getByTestId('cache-entries')).toContainText('lab:v1:public:/catalog/')
  await page.getByTestId('cache-fixture').selectOption('cross-user')
  await expect(page.getByTestId('cache-request-2')).toHaveCount(0)
  const { fixed } = await compare(page, 'cross-user')
  await expect(fixed.getByTestId('cache-entries')).toHaveText('[]')
  await expect(fixed.getByTestId('cache-origin-reads')).toHaveText('2')
})

test('cache: failed and malformed responses show an error and allow a successful retry', async ({ page }) => {
  await page.route('**/api/cache/compare/', route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ error: 'Comparison temporarily unavailable.' }) }), { times: 1 })
  await page.getByTestId('cache-run').click()
  await expect(page.getByRole('alert')).toHaveText('Comparison temporarily unavailable.')
  await expect(page.getByTestId('cache-run')).toBeEnabled()
  await expect(page.getByTestId('cache-request-2')).toHaveCount(0)
  await page.route('**/api/cache/compare/', route => route.fulfill({ status: 200, contentType: 'application/json', body: '{"fixture":"private-control","results":{"vulnerable":{},"fixed":{}}}' }), { times: 1 })
  await page.getByTestId('cache-run').click()
  await expect(page.getByRole('alert')).toHaveText('The server returned an unexpected cache comparison.')
  await compare(page, 'public-control')
  await expect(page.getByRole('alert')).toHaveCount(0)
})

test('cache: leaving the tab aborts pending work and a remount starts empty', async ({ page }) => {
  let intercepted
  const requestArrived = new Promise(resolve => { intercepted = resolve })
  let release
  const finish = new Promise(resolve => { release = resolve })
  await page.route('**/api/cache/compare/', async route => {
    intercepted()
    await finish
    try { await route.fulfill({ status: 503, contentType: 'application/json', body: '{"error":"Late failure must not appear"}' }) } catch { /* The component aborted this request. */ }
  }, { times: 1 })
  await page.getByTestId('cache-run').click()
  await requestArrived
  await expect(page.getByTestId('cache-fixture')).toBeDisabled()
  await page.getByTestId('nav-xss').click()
  release()
  await page.getByTestId('nav-cache').click()
  await expect(page.getByTestId('cache-run')).toBeEnabled()
  await expect(page.getByTestId('cache-request-2')).toHaveCount(0)
  await expect(page.getByRole('alert')).toHaveCount(0)
  await compare(page, 'private-control')
})
