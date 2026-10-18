import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-preflight').click()
})

async function compare(page, fixture) {
  await page.getByTestId('preflight-fixture').selectOption(fixture)
  await page.getByTestId('preflight-run').click()
  await expect(page.getByTestId('preflight-fixed-result').getByTestId('preflight-options')).toBeVisible()
  await expect(page.getByTestId('preflight-run')).toBeEnabled()
}

async function expectState(page, mode, { actual = 1, mutations = 1, readable = 'Yes', status = '200', authorization = 'allowed' } = {}) {
  const result = page.getByTestId(`preflight-${mode}-result`)
  await expect(result.getByTestId('preflight-options')).toHaveText('1')
  await expect(result.getByTestId('preflight-cookie')).toHaveText('No')
  await expect(result.getByTestId('preflight-actual')).toHaveText(String(actual))
  await expect(result.getByTestId('preflight-mutations')).toHaveText(String(mutations))
  await expect(result.getByTestId('preflight-readable')).toHaveText(readable)
  await expect(result.getByTestId('preflight-status')).toHaveText(status)
  await expect(result.getByTestId('preflight-authorization')).toHaveText(authorization)
}

test('allowed JSON and custom-header request preflights then mutates and is readable', async ({ page }) => {
  const actualResponse = page.waitForResponse(response => response.url().includes('/api/preflight/probe/fixed/') && response.request().method() === 'POST')
  await compare(page, 'allowed')
  await expectState(page, 'vulnerable')
  await expectState(page, 'fixed')
  const response = await actualResponse
  expect(response.status()).toBe(200)
  expect(response.headers()['access-control-allow-origin']).toBe('http://127.0.0.1:8767')
  expect(response.request().postDataJSON()).toEqual({ action: 'increment' })
  expect(new URL(response.request().frame().url()).origin).toBe('http://127.0.0.1:8767')
  await expect(page.getByTestId('preflight-fixed-result').getByTestId('preflight-marker')).toHaveText('PREFLIGHT_LOCAL_MARKER')
})

for (const fixture of ['denied-method', 'denied-header', 'denied-origin']) {
  test(`${fixture}: real preflight refusal prevents the actual fixed handler`, async ({ page }) => {
    await compare(page, fixture)
    await expectState(page, 'vulnerable')
    await expectState(page, 'fixed', { actual: 0, mutations: 0, readable: 'No', status: 'Unavailable', authorization: 'not reached' })
    await expect(page.getByTestId('preflight-fixed-result').getByTestId('preflight-method')).toHaveText(fixture === 'denied-method' ? 'PUT' : 'POST')
    await expect(page.getByTestId('preflight-fixed-result').getByTestId('preflight-marker')).toHaveText('None')
  })
}

test('missing actual response CORS hides a successful mutation from companion JavaScript', async ({ page }) => {
  await compare(page, 'missing-response-cors')
  await expectState(page, 'vulnerable', { readable: 'No', status: 'Unavailable' })
  await expectState(page, 'fixed')
})

test('readable permission denial is separate from successful CORS preflight', async ({ page }) => {
  await compare(page, 'auth-denied')
  await expectState(page, 'vulnerable', { authorization: 'skipped (vulnerable)' })
  await expectState(page, 'fixed', { mutations: 0, status: '403', authorization: 'denied' })
  await expect(page.getByTestId('preflight-fixed-result').getByTestId('preflight-marker')).toHaveText('PREFLIGHT_PERMISSION_DENIED')
})

test('fresh runs avoid previous grants and preserve allowed positive control after denial', async ({ page }) => {
  await compare(page, 'denied-header')
  const first = await page.getByTestId('preflight-frame').getAttribute('src')
  await compare(page, 'allowed')
  const second = await page.getByTestId('preflight-frame').getAttribute('src')
  expect(new URL(first).searchParams.get('run')).not.toBe(new URL(second).searchParams.get('run'))
  await expectState(page, 'fixed')
  await compare(page, 'allowed')
  await expectState(page, 'fixed')
  expect(await page.getByTestId('preflight-frame').getAttribute('src')).not.toBe(second)
})

test('malformed server evidence produces an error and supports retry without render failure', async ({ page }) => {
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  await page.route('**/api/preflight/state/**', async route => {
    const response = await route.fetch()
    const body = await response.json()
    body.modes.fixed.requestedHeaders = null
    await route.fulfill({ response, json: body })
  })
  await page.getByTestId('preflight-run').click()
  await expect(page.getByRole('alert')).toHaveText('Unexpected server evidence.')
  await expect(page.getByTestId('preflight-run')).toBeEnabled()
  expect(errors).toEqual([])
  await page.unroute('**/api/preflight/state/**')
  await compare(page, 'allowed')
  await expectState(page, 'fixed')
})

test('late preparation after leaving the tab cannot mount a stale companion', async ({ page }) => {
  let release
  let markEntered
  const entered = new Promise(resolve => { markEntered = resolve })
  const gate = new Promise(resolve => { release = resolve })
  await page.route('**/api/preflight/prepare/', async route => {
    const response = await route.fetch()
    markEntered()
    await gate
    try { await route.fulfill({ response }) } catch { /* The component aborted the request. */ }
  })
  await page.getByTestId('preflight-run').click()
  await entered
  await page.getByTestId('nav-xss').click()
  release()
  await expect(page.getByTestId('preflight-frame')).toHaveCount(0)
  await page.getByTestId('nav-preflight').click()
  await expect(page.getByTestId('preflight-frame')).toHaveCount(0)
  await expect(page.getByTestId('preflight-run')).toBeEnabled()
})
