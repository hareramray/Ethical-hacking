import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-prototype').click()
  await expect(page.getByTestId('prototype-run')).toBeEnabled()
})

async function compare(page, fixture) {
  await page.getByTestId('prototype-fixture').selectOption(fixture)
  await page.getByTestId('prototype-run').click()
  const vulnerable = page.getByTestId('prototype-vulnerable-result')
  const fixed = page.getByTestId('prototype-fixed-result')
  for (const result of [vulnerable, fixed]) {
    await expect(result.getByTestId('prototype-before')).toHaveText('absent')
    await expect(result.getByTestId('prototype-origin')).toHaveText('null')
  }
  await expect(page.getByTestId('prototype-run')).toBeEnabled()
  return { vulnerable, fixed }
}

async function expectCleanDashboard(page) {
  expect(await page.evaluate(() => ({ own: Object.hasOwn(Object.prototype, 'labTheme'), inherited: 'labTheme' in {} })))
    .toEqual({ own: false, inherited: false })
}

test('prototype: allowed own preference fields survive both paths without pollution', async ({ page }) => {
  const results = await compare(page, 'normal')
  for (const result of Object.values(results)) {
    await expect(result.getByTestId('prototype-accepted')).toHaveText('yes')
    await expect(result.getByTestId('prototype-after')).toHaveText('absent')
    await expect(result.getByTestId('prototype-theme')).toHaveText('ocean')
    await expect(result.getByTestId('prototype-source')).toHaveText('own')
    await expect(result.getByTestId('prototype-font')).toHaveText('large / string')
    await expect(result.getByTestId('prototype-own-keys')).toHaveText('fontSize, labTheme')
    await expect(result.frameLocator('iframe').locator('#theme')).toHaveText('Theme: ocean')
  }
  await expect(results.vulnerable.getByTestId('prototype-null')).toHaveText('no')
  await expect(results.fixed.getByTestId('prototype-null')).toHaveText('yes')
  await expectCleanDashboard(page)
})

test('prototype: both prototype paths and a nested key really modify only the vulnerable frame realm', async ({ page }) => {
  for (const fixture of ['proto', 'constructor', 'nested']) {
    const { vulnerable, fixed } = await compare(page, fixture)
    await expect(vulnerable.getByTestId('prototype-after')).toHaveText('polluted-marker')
    await expect(vulnerable.getByTestId('prototype-theme')).toHaveText('polluted-marker')
    await expect(vulnerable.getByTestId('prototype-source')).toHaveText('inherited')
    await expect(vulnerable.getByTestId('prototype-own-keys')).toHaveText('(none)')
    expect(await vulnerable.frameLocator('iframe').locator('body').evaluate(() => ({
      own: Object.hasOwn(Object.prototype, 'labTheme'), inherited: ({}).labTheme,
    }))).toEqual({ own: true, inherited: 'polluted-marker' })
    await expect(fixed.getByTestId('prototype-after')).toHaveText('absent')
    await expect(fixed.getByTestId('prototype-accepted')).toHaveText('no')
    await expect(fixed.getByTestId('prototype-theme')).toHaveText('default')
    await expect(fixed.getByTestId('prototype-source')).toHaveText('default')
    await expect(fixed.getByTestId('prototype-own-keys')).toHaveText('(none)')
    expect(await fixed.frameLocator('iframe').locator('body').evaluate(() => 'labTheme' in {})).toBe(false)
    await expectCleanDashboard(page)
  }
})

test('prototype: complete preflight rejects mixed input without applying the earlier allowed preference', async ({ page }) => {
  const { vulnerable, fixed } = await compare(page, 'mixed')
  await expect(vulnerable.getByTestId('prototype-after')).toHaveText('polluted-marker')
  await expect(vulnerable.getByTestId('prototype-theme')).toHaveText('sunset')
  await expect(vulnerable.getByTestId('prototype-source')).toHaveText('own')
  await expect(vulnerable.getByTestId('prototype-own-keys')).toHaveText('fontSize, labTheme')
  await expect(fixed.getByTestId('prototype-accepted')).toHaveText('no')
  await expect(fixed.getByTestId('prototype-after')).toHaveText('absent')
  await expect(fixed.getByTestId('prototype-theme')).toHaveText('default')
  await expect(fixed.getByTestId('prototype-font')).toHaveText('normal / undefined')
  await expect(fixed.getByTestId('prototype-own-keys')).toHaveText('(none)')
})

test('prototype: preference types are validated before copying any fields', async ({ page }) => {
  const { vulnerable, fixed } = await compare(page, 'invalid-type')
  await expect(vulnerable.getByTestId('prototype-after')).toHaveText('absent')
  await expect(vulnerable.getByTestId('prototype-theme')).toHaveText('ocean')
  await expect(vulnerable.getByTestId('prototype-font')).toHaveText('42 / number')
  await expect(fixed.getByTestId('prototype-accepted')).toHaveText('no')
  await expect(fixed.getByTestId('prototype-theme')).toHaveText('default')
  await expect(fixed.getByTestId('prototype-own-keys')).toHaveText('(none)')
  await expect(fixed.getByTestId('prototype-reason')).toContainText('font size must be an allowed string')
})

test('prototype: a new comparison discards polluted realms and old frame URLs; direct navigation stays sandboxed', async ({ page, browser }) => {
  const { vulnerable } = await compare(page, 'constructor')
  const oldRun = await page.getByTestId('prototype-run-id').textContent()
  const src = await vulnerable.locator('iframe').getAttribute('src')
  const other = await browser.newContext()
  try { expect((await other.request.get(`http://127.0.0.1:8766${src}`)).status()).toBe(404) }
  finally { await other.close() }
  const direct = await page.context().newPage()
  try {
    const response = await direct.goto(`http://127.0.0.1:8766${src}`)
    expect(response.headers()['content-security-policy']).toContain('sandbox allow-scripts')
    await expect(direct.locator('#theme')).toHaveText('Theme: polluted-marker')
    expect(await direct.evaluate(() => window.origin)).toBe('null')
    expect(await direct.evaluate(() => {
      try { void document.cookie; return false } catch (error) { return error.name === 'SecurityError' }
    })).toBe(true)
  } finally { await direct.close() }
  const fresh = await compare(page, 'normal')
  expect(await page.getByTestId('prototype-run-id').textContent()).not.toBe(oldRun)
  await expect(fresh.vulnerable.getByTestId('prototype-after')).toHaveText('absent')
  expect((await page.request.get(src)).status()).toBe(404)
  await expectCleanDashboard(page)
  await page.getByTestId('nav-xss').click()
  await page.getByTestId('nav-prototype').click()
  await expect(page.getByTestId('prototype-frame')).toHaveCount(0)
})

test('prototype: the dashboard ignores stale, wrong-source, wrong-origin, and malformed telemetry', async ({ page }) => {
  await compare(page, 'proto')
  const oldRun = await page.getByTestId('prototype-run-id').textContent()
  const { fixed } = await compare(page, 'normal')
  const run = await page.getByTestId('prototype-run-id').textContent()
  const evidence = JSON.parse(await fixed.frameLocator('iframe').locator('#prototype-evidence').textContent())
  await page.evaluate(({ oldRun, run, evidence }) => {
    const frame = document.querySelector('[data-testid="prototype-fixed-result"] iframe')
    const data = { type: 'prototype-observation', mode: 'fixed', run, evidence: { ...evidence, selectedTheme: 'sunset' } }
    const send = (origin, source, message) => window.dispatchEvent(new MessageEvent('message', { origin, source, data: message }))
    send(location.origin, frame.contentWindow, data)
    send('null', window, data)
    send('null', frame.contentWindow, { ...data, run: oldRun })
    send('null', frame.contentWindow, { ...data, extra: true })
    send('null', frame.contentWindow, { ...data, evidence: { ...data.evidence, extra: true } })
    send('null', frame.contentWindow, { ...data, evidence: { ...data.evidence, reason: 'x'.repeat(241) } })
  }, { oldRun, run, evidence })
  await expect(fixed.getByTestId('prototype-theme')).toHaveText('ocean')
  await expect(fixed.getByTestId('prototype-after')).toHaveText('absent')
})
