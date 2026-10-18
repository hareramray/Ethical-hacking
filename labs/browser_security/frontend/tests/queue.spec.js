import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-queue').click()
})

async function compare(page, fixture) {
  await page.getByTestId('queue-fixture').selectOption(fixture)
  await page.getByTestId('queue-run').click()
  const vulnerable = page.getByTestId('queue-vulnerable-result')
  const fixed = page.getByTestId('queue-fixed-result')
  await expect(vulnerable.getByTestId('queue-jobs')).toBeVisible()
  await expect(fixed.getByTestId('queue-jobs')).toBeVisible()
  await expect(page.getByTestId('queue-run')).toBeEnabled()
  return { vulnerable, fixed }
}

test('queue: an authorized control creates and delivers one stored export', async ({ page }) => {
  const results = await compare(page, 'normal')
  await expect(page.getByTestId('queue-actor')).toContainText('user-ada')
  await expect(page.getByTestId('queue-downloader')).toContainText('user-ada / tenant-blue')
  for (const result of Object.values(results)) {
    await expect(result.locator('.traversal-outcome')).toHaveText('delivered')
    await expect(result.getByTestId('queue-job-count')).toHaveText('1')
    await expect(result.getByTestId('queue-job-state')).toHaveText('completed')
    await expect(result.getByTestId('queue-artifact-count')).toHaveText('1')
    await expect(result.getByTestId('queue-delivered')).toHaveText('FICTIONAL-ADA-BLUE-EXPORT')
    await expect(result.getByTestId('queue-events').locator('li')).toHaveCount(3)
  }
})

test('queue: revocation before worker blocks creation despite a saved enqueue grant', async ({ page }) => {
  const { vulnerable, fixed } = await compare(page, 'revoke-before-worker')
  await expect(vulnerable.getByTestId('queue-delivered')).toHaveText('FICTIONAL-ADA-BLUE-EXPORT')
  await expect(vulnerable.getByTestId('queue-artifact-count')).toHaveText('1')
  await expect(fixed.getByTestId('queue-jobs')).toContainText('"granted_at_enqueue": 1')
  await expect(fixed.getByTestId('queue-job-state')).toHaveText('denied')
  await expect(fixed.getByTestId('queue-job-count')).toHaveText('1')
  await expect(fixed.getByTestId('queue-artifact-count')).toHaveText('0')
  await expect(fixed.getByTestId('queue-delivered')).toHaveText('(none)')
  await expect(fixed.getByTestId('queue-events')).toContainText('worker: denied')
  await expect(fixed.getByTestId('queue-submitter-permission')).toHaveText('revoked')
})

test('queue: revocation before download denies delivery while preserving artifact evidence', async ({ page }) => {
  const { vulnerable, fixed } = await compare(page, 'revoke-before-download')
  for (const result of [vulnerable, fixed]) {
    await expect(result.getByTestId('queue-job-state')).toHaveText('completed')
    await expect(result.getByTestId('queue-artifact-count')).toHaveText('1')
    await expect(result.getByTestId('queue-events')).toContainText('worker: created')
    await expect(result.getByTestId('queue-downloader-permission')).toHaveText('revoked')
  }
  await expect(vulnerable.getByTestId('queue-delivered')).toHaveText('FICTIONAL-ADA-BLUE-EXPORT')
  await expect(fixed.getByTestId('queue-delivered')).toHaveText('(none)')
  await expect(fixed.getByTestId('queue-events')).toContainText('download: denied')
})

test('queue: owner and tenant are required even when the downloader has export permission', async ({ page }) => {
  for (const [fixture, identity] of [['peer-download', 'user-bea / tenant-blue'], ['cross-tenant-download', 'user-ada / tenant-amber']]) {
    const { vulnerable, fixed } = await compare(page, fixture)
    await expect(page.getByTestId('queue-downloader')).toContainText(identity)
    await expect(vulnerable.getByTestId('queue-delivered')).toHaveText('FICTIONAL-ADA-BLUE-EXPORT')
    await expect(fixed.getByTestId('queue-downloader-permission')).toHaveText('allowed')
    await expect(fixed.getByTestId('queue-artifacts')).toContainText('"owner": "user-ada"')
    await expect(fixed.getByTestId('queue-artifacts')).toContainText('"tenant": "tenant-blue"')
    await expect(fixed.getByTestId('queue-delivered')).toHaveText('(none)')
  }
})

test('queue: initial denial creates nothing and fixture selection clears old results', async ({ page }) => {
  const results = await compare(page, 'initially-denied')
  for (const result of Object.values(results)) {
    await expect(result.getByTestId('queue-job-count')).toHaveText('0')
    await expect(result.getByTestId('queue-artifact-count')).toHaveText('0')
    await expect(result.getByTestId('queue-delivered')).toHaveText('(none)')
    await expect(result.getByTestId('queue-events')).toContainText('enqueue: denied')
  }
  await page.getByTestId('queue-fixture').selectOption('normal')
  await expect(page.getByTestId('queue-jobs')).toHaveCount(0)
  const { fixed } = await compare(page, 'normal')
  await expect(fixed.getByTestId('queue-submitter-permission')).toHaveText('allowed')
  await expect(fixed.getByTestId('queue-delivered')).toHaveText('FICTIONAL-ADA-BLUE-EXPORT')
})

test('queue: a failed response clears evidence and permits a successful retry', async ({ page }) => {
  await compare(page, 'normal')
  await page.route('**/api/queue/compare/', route => route.fulfill({ status: 503, contentType: 'text/plain', body: 'Unavailable' }), { times: 1 })
  await page.getByTestId('queue-run').click()
  await expect(page.getByRole('alert')).toContainText('HTTP 503: no JSON result was returned.')
  await expect(page.getByTestId('queue-jobs')).toHaveCount(0)
  await expect(page.getByTestId('queue-run')).toBeEnabled()
  const { fixed } = await compare(page, 'normal')
  await expect(fixed.getByTestId('queue-delivered')).toHaveText('FICTIONAL-ADA-BLUE-EXPORT')
  await expect(page.getByRole('alert')).toHaveCount(0)
})

test('queue: navigating away discards a delayed response without stale evidence', async ({ page }) => {
  let release
  const paused = new Promise(resolve => { release = resolve })
  let arrived
  const pending = new Promise(resolve => { arrived = resolve })
  let finished
  const handled = new Promise(resolve => { finished = resolve })
  await page.route('**/api/queue/compare/', async route => {
    const response = await route.fetch()
    arrived()
    await paused
    try { await route.fulfill({ response }) } catch { /* The old component aborted this request. */ }
    finally { finished() }
  }, { times: 1 })
  await page.getByTestId('queue-run').click()
  await pending
  await page.getByTestId('nav-csp').click()
  release()
  await handled
  await page.getByTestId('nav-queue').click()
  await expect(page.getByTestId('queue-run')).toBeEnabled()
  await expect(page.getByTestId('queue-jobs')).toHaveCount(0)
  await expect(page.getByRole('alert')).toHaveCount(0)
})
