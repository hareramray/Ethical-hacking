import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-redirect').click()
  await expect(page.getByTestId('redirect-run')).toBeEnabled()
})

async function compare(page, fixture) {
  await page.getByTestId('redirect-fixture').selectOption(fixture)
  const responses = Object.fromEntries(['vulnerable', 'fixed'].map(mode => [mode, page.waitForResponse(response => {
    const url = new URL(response.url())
    return url.pathname === '/lab/redirect/go/' && url.searchParams.get('fixture') === fixture && url.searchParams.get('mode') === mode
  })]))
  await page.getByTestId('redirect-run').click()
  const result = {}
  for (const mode of ['vulnerable', 'fixed']) {
    const response = await responses[mode]
    const panel = page.getByTestId(`redirect-${mode}-result`)
    await expect(panel.locator('.traversal-outcome')).toBeVisible()
    result[mode] = { response, panel }
  }
  await expect(page.getByTestId('redirect-run')).toBeEnabled()
  return result
}

async function assertLanded(page, mode, result, destination, marker) {
  expect(result.response.status()).toBe(302)
  const location = result.response.headers().location
  expect(location).toBeTruthy()
  const expectedUrl = new URL(location, result.response.url()).href
  await expect(result.panel.getByTestId('redirect-destination')).toHaveText(destination)
  await expect(result.panel.getByTestId('redirect-marker')).toHaveText(marker)
  await expect(result.panel.getByTestId('redirect-final-url')).toHaveText(expectedUrl)
  const markerFrame = page.frameLocator(`[data-testid="redirect-${mode}-frame"]`)
  await expect(markerFrame.locator('#marker')).toHaveText(marker)
  expect(page.frames().some(frame => frame.url() === expectedUrl)).toBe(true)
  expect(await page.getByTestId(`redirect-${mode}-frame`).getAttribute('sandbox')).toBe('allow-scripts')
  return expectedUrl
}

async function assertRefused(page, result) {
  expect(result.response.status()).toBe(400)
  expect(result.response.headers().location).toBeUndefined()
  await expect(result.panel.locator('.traversal-outcome')).toHaveText('rejected')
  await expect(result.panel.getByTestId('redirect-marker')).toHaveText('RETURN_URL_REJECTED')
  await expect(result.panel.getByTestId('redirect-final-url')).toHaveText(result.response.url())
  await expect(page.frameLocator('[data-testid="redirect-fixed-frame"]').locator('#marker')).toHaveText('RETURN_URL_REJECTED')
  expect(page.frames().some(frame => frame.url() === result.response.url())).toBe(true)
}

test('redirect: the permitted relative return path produces a real 302 and landing in both modes', async ({ page }) => {
  const results = await compare(page, 'allowed')
  for (const mode of ['vulnerable', 'fixed']) {
    const url = await assertLanded(page, mode, results[mode], 'main', 'MAIN_RETURN_MARKER')
    expect(new URL(url).origin).toBe(new URL(page.url()).origin)
    expect(results[mode].response.headers().location).toMatch(/^\/lab\/redirect\/landing\/\?/)
  }
})

for (const fixture of ['absolute-peer', 'scheme-relative-peer']) {
  test(`redirect: ${fixture} reaches the actual companion while the fixed handler refuses`, async ({ page }) => {
    const results = await compare(page, fixture)
    const destination = await assertLanded(page, 'vulnerable', results.vulnerable, 'peer', 'COMPANION_RETURN_MARKER')
    expect(new URL(destination).origin).not.toBe(new URL(page.url()).origin)
    const header = results.vulnerable.response.headers().location
    expect(header.startsWith(fixture === 'absolute-peer' ? 'http://' : '//')).toBe(true)
    await assertRefused(page, results.fixed)
    const peer = new URL(destination).origin
    expect((await page.request.get(peer + '/api/bootstrap')).status()).toBe(404)
    expect((await page.request.get(peer + '/api/redirect/prepare/')).status()).toBe(404)
    expect((await page.request.get(peer + '/lab/redirect/go/')).status()).toBe(404)
    expect(page.url()).toBe(new URL('/', results.vulnerable.response.url()).href)
  })
}

test('redirect: the browser normalizes dot segments but the exact-path rule rejects the alternate spelling', async ({ page }) => {
  const results = await compare(page, 'normalized-path')
  expect(results.vulnerable.response.headers().location).toContain('/discard/../landing/')
  const destination = await assertLanded(page, 'vulnerable', results.vulnerable, 'main', 'MAIN_RETURN_MARKER')
  expect(new URL(destination).pathname).toBe('/lab/redirect/landing/')
  expect(destination).not.toContain('/discard/')
  await assertRefused(page, results.fixed)
})

test('redirect: rerunning replaces old frames and mismatched marker messages cannot overwrite results', async ({ page }) => {
  const first = await compare(page, 'allowed')
  const oldUrl = first.fixed.response.url()
  const run = new URL(first.vulnerable.response.url()).searchParams.get('run')
  const actualFrame = page.frames().find(frame => frame.url().includes('/lab/redirect/landing/') && new URL(frame.url()).searchParams.get('mode') === 'vulnerable')
  expect(actualFrame).toBeTruthy()
  // This has the real source window and opaque origin, but an invalid schema/result.
  await actualFrame.evaluate(({ run, main }) => parent.postMessage({ channel: 'redirect-lesson-result', runId: run,
    fixture: 'allowed', mode: 'vulnerable', evidence: { outcome: 'landed', destination: 'peer', marker: 'FAKE', finalUrl: location.href } }, main), { run, main: new URL(page.url()).origin })
  await expect(first.vulnerable.panel.getByTestId('redirect-marker')).toHaveText('MAIN_RETURN_MARKER')
  const next = await compare(page, 'absolute-peer')
  expect(next.fixed.response.url()).not.toBe(oldUrl)
  expect(page.frames().some(frame => frame.url().includes(`run=${run}`))).toBe(false)
  await assertLanded(page, 'vulnerable', next.vulnerable, 'peer', 'COMPANION_RETURN_MARKER')
  await assertRefused(page, next.fixed)
})

test('redirect: leaving during preparation does not create late frames', async ({ page }) => {
  let release
  const held = new Promise(resolve => { release = resolve })
  let started
  const intercepted = new Promise(resolve => { started = resolve })
  await page.route('**/api/redirect/prepare/', async route => {
    const response = await route.fetch()
    started()
    await held
    await route.fulfill({ response }).catch(() => {})
  })
  await page.getByTestId('redirect-run').click()
  await intercepted
  await page.getByTestId('nav-csp').click()
  release()
  await expect(page.getByTestId('redirect-vulnerable-frame')).toHaveCount(0)
  await page.getByTestId('nav-redirect').click()
  await expect(page.getByTestId('redirect-run')).toBeEnabled()
  await expect(page.getByTestId('redirect-vulnerable-frame')).toHaveCount(0)
})
