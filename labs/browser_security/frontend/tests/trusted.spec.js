import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-trusted').click()
  await expect(page.getByTestId('trusted-run')).toBeEnabled()
})

async function run(page, fixture, status = 'complete') {
  await page.getByTestId('trusted-fixture').selectOption(fixture)
  await page.getByTestId('trusted-run').click()
  const vulnerable = page.getByTestId('trusted-vulnerable-result')
  const fixed = page.getByTestId('trusted-fixed-result')
  for (const result of [vulnerable, fixed]) await expect(result.getByTestId('trusted-status')).toHaveText(status)
  await expect(page.getByTestId('trusted-pending')).toHaveCount(0)
  return { vulnerable, fixed }
}

test('trusted: sanitizer-backed TrustedHTML preserves actual useful formatting', async ({ page }) => {
  const headers = page.waitForResponse(response => response.url().includes('/lab/trusted/frame/') && response.url().includes('mode=fixed'))
  const { vulnerable, fixed } = await run(page, 'formatting')
  for (const result of [vulnerable, fixed]) {
    await expect(result.getByTestId('trusted-sink')).toHaveText('accepted')
    await expect(result.getByTestId('trusted-type')).toHaveText('yes')
    await expect(result.getByTestId('trusted-guard')).toHaveText('blocked')
    await expect(result.getByTestId('trusted-formatting')).toHaveText('yes')
    await expect(result.frameLocator('iframe').locator('#fixture-output strong')).toHaveText('reader')
    await expect(result.frameLocator('iframe').locator('#fixture-output em')).toHaveText('useful')
    await expect(result.frameLocator('iframe').locator('#fixture-output code')).toHaveText('formatting')
    await expect(result.getByTestId('trusted-marker')).toHaveText('No marker received')
    await expect(result.locator('iframe')).toHaveAttribute('sandbox', 'allow-scripts')
  }
  const policy = (await headers).headers()['content-security-policy']
  expect(policy).toContain("require-trusted-types-for 'script'")
  expect(policy).toContain('trusted-types lab-sanitize dompurify')
  expect(policy).not.toContain('allow-same-origin')
})

test('trusted: encoded markup remains text in both actual frame DOMs', async ({ page }) => {
  const { vulnerable, fixed } = await run(page, 'text')
  for (const result of [vulnerable, fixed]) {
    await expect(result.getByTestId('trusted-text')).toHaveText('<strong>just text</strong>')
    await expect(result.frameLocator('iframe').locator('#fixture-output')).toHaveText('<strong>just text</strong>')
    await expect(result.frameLocator('iframe').locator('#fixture-output strong')).toHaveCount(0)
    await expect(result.getByTestId('trusted-formatting')).toHaveText('no')
  }
})

test('trusted: accepted pass-through value executes only the harmless marker while sanitizer strips the event', async ({ page }) => {
  const external = []
  page.on('request', request => { if (!request.url().startsWith('http://127.0.0.1:8766/') && !request.url().startsWith('data:')) external.push(request.url()) })
  const { vulnerable, fixed } = await run(page, 'event')
  for (const result of [vulnerable, fixed]) {
    await expect(result.getByTestId('trusted-sink')).toHaveText('accepted')
    await expect(result.getByTestId('trusted-type')).toHaveText('yes')
    await expect(result.getByTestId('trusted-formatting')).toHaveText('yes')
  }
  await expect(vulnerable.getByTestId('trusted-marker')).toHaveText('HARMLESS_TT_MARKER')
  await expect(vulnerable.frameLocator('iframe').locator('#event-marker')).toHaveText('HARMLESS_TT_MARKER')
  await expect(vulnerable.frameLocator('iframe').locator('#fixture-output img')).toHaveCount(1)
  await expect(fixed.getByTestId('trusted-marker')).toHaveText('No marker received')
  await expect(fixed.frameLocator('iframe').locator('#event-marker')).toBeEmpty()
  await expect(fixed.frameLocator('iframe').locator('#fixture-output img, #fixture-output [onerror]')).toHaveCount(0)
  expect(external).toEqual([])
})

test('trusted: both enforced sinks reject a raw string without policy conversion', async ({ page }) => {
  const { vulnerable, fixed } = await run(page, 'raw-string')
  for (const result of [vulnerable, fixed]) {
    await expect(result.getByTestId('trusted-policy')).toHaveText('not-attempted')
    await expect(result.getByTestId('trusted-sink')).toHaveText('rejected')
    await expect(result.getByTestId('trusted-type')).toHaveText('no')
    await expect(result.getByTestId('trusted-events')).toContainText('require-trusted-types-for')
    await expect(result.frameLocator('iframe').locator('#fixture-output')).toBeEmpty()
  }
})

test('trusted: policy-name allowlists reject creation before any sink assignment', async ({ page }) => {
  const { vulnerable, fixed } = await run(page, 'forbidden-policy')
  for (const result of [vulnerable, fixed]) {
    await expect(result.getByTestId('trusted-policy')).toHaveText('rejected')
    await expect(result.getByTestId('trusted-sink')).toHaveText('not-attempted')
    await expect(result.getByTestId('trusted-events')).toContainText('trusted-types')
    await expect(result.frameLocator('iframe').locator('#fixture-output')).toBeEmpty()
  }
})

test('trusted: hiding the API reports unsupported and never runs an unprotected fixture', async ({ page }) => {
  await page.addInitScript(() => { Object.defineProperty(window, 'trustedTypes', { configurable: true, value: undefined }) })
  const { vulnerable, fixed } = await run(page, 'event', 'unsupported')
  for (const result of [vulnerable, fixed]) {
    await expect(result.getByTestId('trusted-detail')).toContainText('API unavailable')
    await expect(result.getByTestId('trusted-sink')).toHaveText('not-attempted')
    await expect(result.getByTestId('trusted-marker')).toHaveText('No marker received')
    await expect(result.frameLocator('iframe').locator('#fixture-output')).toBeEmpty()
  }
})

test('trusted: session ownership, fresh runs, and strict frame message validation', async ({ page, browser }) => {
  const { fixed } = await run(page, 'text')
  const oldRun = await page.getByTestId('trusted-run-id').textContent()
  const oldSrc = await fixed.locator('iframe').getAttribute('src')
  const other = await browser.newContext()
  try { expect((await other.request.get(`http://127.0.0.1:8766${oldSrc}`)).status()).toBe(404) }
  finally { await other.close() }
  await page.evaluate(run => {
    const frame = document.querySelector('[data-testid="trusted-fixed-result"] iframe')
    const data = { type: 'trusted-observation', run, mode: 'fixed', evidence: { status: 'complete', rawGuard: 'blocked', policy: 'created', sink: 'accepted', trusted: true, formatting: false, text: 'forged', marker: 'HARMLESS_TT_MARKER', events: [], detail: 'forged' } }
    for (const variant of [
      { origin: location.origin, source: frame.contentWindow, data },
      { origin: 'null', source: window, data },
      { origin: 'null', source: frame.contentWindow, data: { ...data, run: '0'.repeat(32) } },
      { origin: 'null', source: frame.contentWindow, data: { ...data, extra: true } },
      { origin: 'null', source: frame.contentWindow, data: { ...data, evidence: { ...data.evidence, text: 'x'.repeat(401) } } },
      { origin: 'null', source: frame.contentWindow, data: { ...data, evidence: { ...data.evidence, rawGuard: 'accepted' } } },
    ]) window.dispatchEvent(new MessageEvent('message', variant))
  }, oldRun)
  await expect(fixed.getByTestId('trusted-marker')).toHaveText('No marker received')
  await expect(fixed.getByTestId('trusted-text')).toHaveText('<strong>just text</strong>')
  await run(page, 'formatting')
  expect(await page.getByTestId('trusted-run-id').textContent()).not.toBe(oldRun)
  expect((await page.request.get(oldSrc)).status()).toBe(404)
  await page.getByTestId('nav-csp').click()
  await page.getByTestId('nav-trusted').click()
  await expect(page.getByTestId('trusted-frame')).toHaveCount(0)
})

test('trusted: leaving during preparation discards delayed frames', async ({ page }) => {
  let release, arrived
  const paused = new Promise(resolve => { release = resolve })
  const pending = new Promise(resolve => { arrived = resolve })
  await page.route('**/api/trusted/prepare/', async route => {
    const response = await route.fetch()
    arrived()
    await paused
    try { await route.fulfill({ response }) } catch { /* The component aborted its request. */ }
  })
  await page.getByTestId('trusted-run').click()
  await pending
  await page.getByTestId('nav-csp').click()
  release()
  await page.getByTestId('nav-trusted').click()
  await expect(page.getByTestId('trusted-run')).toBeEnabled()
  await expect(page.getByTestId('trusted-frame')).toHaveCount(0)
  await expect(page.getByTestId('trusted-pending')).toHaveCount(0)
})
