import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-cross-origin').click()
})

async function start(page, lesson) {
  await page.getByTestId('cross-origin-lesson').selectOption(lesson)
  await page.getByTestId('cross-origin-run').click()
  await expect(page.getByTestId('cross-origin-vulnerable').getByTestId('peer-readability')).toBeVisible()
  await expect(page.getByTestId('cross-origin-run')).toBeEnabled()
}

test('CSRF: unreadable peer responses still change only the vulnerable counter', async ({ page }) => {
  const sent = page.waitForRequest(request => request.url().includes('/change/vulnerable/') && request.method() === 'POST')
  await start(page, 'csrf')
  const request = await sent
  // Chrome can omit Origin from Playwright's header view for a CORS-blocked
  // response. Verify the initiating frame's real origin instead.
  expect(new URL(request.frame().url()).origin).toBe('http://127.0.0.1:8767')
  expect((await request.allHeaders())['x-csrftoken']).toBeUndefined()
  expect(request.postData()).toBe('action=increment')
  const vulnerable = page.getByTestId('cross-origin-vulnerable')
  const fixed = page.getByTestId('cross-origin-fixed')
  await expect(vulnerable.getByTestId('peer-readability')).toHaveText('Unreadable')
  await expect(fixed.getByTestId('peer-readability')).toHaveText('Unreadable')
  await expect(vulnerable.getByTestId('server-counter')).toHaveText('1')
  await expect(fixed.getByTestId('server-counter')).toHaveText('0')
  await page.getByTestId('cross-origin-legitimate').click()
  await expect(page.getByTestId('cross-origin-legitimate-result')).toContainText('HTTP 200')
  await expect(fixed.getByTestId('server-counter')).toHaveText('1')
  // Starting again resets only the lesson's synthetic counters.
  await start(page, 'csrf')
  await expect(vulnerable.getByTestId('server-counter')).toHaveText('1')
  await expect(fixed.getByTestId('server-counter')).toHaveText('0')
})

test('CORS: only the deliberately allowed peer can read its synthetic response', async ({ page }) => {
  await start(page, 'cors')
  const vulnerable = page.getByTestId('cross-origin-vulnerable')
  const fixed = page.getByTestId('cross-origin-fixed')
  await expect(vulnerable.getByTestId('peer-readability')).toHaveText('Readable')
  await expect(vulnerable.getByTestId('peer-marker')).toHaveText('CORS_SYNTHETIC_SECRET')
  await expect(fixed.getByTestId('peer-readability')).toHaveText('Unreadable')
  await expect(fixed.getByTestId('peer-marker')).toHaveText('No marker readable')
  const peerUrl = await page.getByTestId('cross-origin-frame').getAttribute('src')
  const run = new URL(peerUrl).searchParams.get('run')
  const sameOrigin = await page.evaluate(async (runId) => {
    const response = await fetch('/api/cross-origin/data/fixed/?run=' + encodeURIComponent(runId))
    return { status: response.status, body: await response.json() }
  }, run)
  expect(sameOrigin).toMatchObject({ status: 200, body: { marker: 'CORS_SYNTHETIC_SECRET' } })
  const frame = page.frames().find(item => item.url() === peerUrl)
  expect(await frame.evaluate(() => location.origin)).toBe('http://127.0.0.1:8767')
})

test('the companion cannot serve the dashboard APIs and results use a fresh run', async ({ page }) => {
  expect((await page.request.get('http://127.0.0.1:8767/api/health')).status()).toBe(200)
  expect((await page.request.get('http://127.0.0.1:8767/api/bootstrap')).status()).toBe(404)
  expect((await page.request.get('http://127.0.0.1:8767/')).status()).toBe(404)
  await start(page, 'cors')
  const first = await page.getByTestId('cross-origin-frame').getAttribute('src')
  await start(page, 'csrf')
  expect(await page.getByTestId('cross-origin-frame').getAttribute('src')).not.toBe(first)
  await expect(page.getByTestId('cross-origin-vulnerable')).not.toContainText('CORS_SYNTHETIC_SECRET')
  await expect(page.getByTestId('cross-origin-fixed').getByTestId('server-counter')).toHaveText('0')
})
