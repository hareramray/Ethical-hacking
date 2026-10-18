import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-clobber').click()
  await expect(page.getByTestId('clobber-run')).toBeEnabled()
})

async function compare(page, fixture) {
  await page.getByTestId('clobber-fixture').selectOption(fixture)
  await page.getByTestId('clobber-run').click()
  const vulnerable = page.getByTestId('clobber-vulnerable-result')
  const fixed = page.getByTestId('clobber-fixed-result')
  for (const result of [vulnerable, fixed]) {
    await expect(result.getByTestId('clobber-label')).toBeVisible()
    await expect(result.getByTestId('clobber-note')).toHaveText('Hello from a scoped field')
    await expect(result.frameLocator('iframe').locator('#observed-note')).toHaveText('Hello from a scoped field')
  }
  return { vulnerable, fixed }
}

test('clobber: ordinary markup preserves intended configuration and a legitimate field', async ({ page }) => {
  const results = await compare(page, 'normal')
  for (const result of Object.values(results)) {
    await expect(result.getByTestId('clobber-config-type')).toHaveText('undefined')
    await expect(result.getByTestId('clobber-preview-type')).toHaveText('undefined')
    await expect(result.getByTestId('clobber-method-type')).toHaveText('String')
    await expect(result.getByTestId('clobber-label')).toHaveText('Standard view | method: post')
    await expect(result.frameLocator('iframe').locator('article strong')).toHaveText('ordinary note')
    await expect(result.frameLocator('iframe').locator('#observed-label')).toHaveText('Standard view | method: post')
  }
})

test('clobber: real named window and form lookups change only the vulnerable display', async ({ page }) => {
  let results = await compare(page, 'named-config')
  for (const result of Object.values(results)) {
    await expect(result.getByTestId('clobber-config-type')).toHaveText('HTMLFormElement')
    await expect(result.getByTestId('clobber-preview-type')).toHaveText('HTMLInputElement')
    expect(await result.frameLocator('iframe').locator('#labConfig').evaluate(element => element === window.labConfig && window.labConfig.preview instanceof HTMLInputElement)).toBe(true)
  }
  await expect(results.vulnerable.getByTestId('clobber-label')).toHaveText('Preview mode | method: post')
  await expect(results.fixed.getByTestId('clobber-label')).toHaveText('Standard view | method: post')
  await expect(results.vulnerable.frameLocator('iframe').locator('#observed-label')).toHaveText('Preview mode | method: post')
  await expect(results.fixed.frameLocator('iframe').locator('#observed-label')).toHaveText('Standard view | method: post')

  results = await compare(page, 'form-property')
  for (const result of Object.values(results)) {
    await expect(result.getByTestId('clobber-method-type')).toHaveText('HTMLInputElement')
    const form = result.frameLocator('iframe').locator('form[data-owned-form="note"]')
    expect(await form.evaluate(element => element.method instanceof HTMLInputElement && element.method.value === 'HARMLESS_METHOD_MARKER')).toBe(true)
    await expect(form).toHaveAttribute('method', 'post')
  }
  await expect(results.vulnerable.getByTestId('clobber-label')).toHaveText('Standard view | method: [object HTMLInputElement]')
  await expect(results.fixed.getByTestId('clobber-label')).toHaveText('Standard view | method: post')
  expect(await page.evaluate(() => typeof window.labConfig)).toBe('undefined')
  await expect(page.locator('input[name="method"]')).toHaveCount(0)
})

test('clobber: embedded and direct frames stay opaque and another session cannot read a run', async ({ page, browser }) => {
  const { vulnerable } = await compare(page, 'named-config')
  const src = await vulnerable.locator('iframe').getAttribute('src')
  expect(await vulnerable.frameLocator('iframe').locator('body').evaluate(() => {
    try { void parent.document; return false } catch (error) { return error.name === 'SecurityError' }
  })).toBe(true)
  const other = await browser.newContext()
  try {
    expect((await other.request.get(`http://127.0.0.1:8766${src}`)).status()).toBe(404)
  } finally { await other.close() }
  const direct = await page.context().newPage()
  try {
    const response = await direct.goto(`http://127.0.0.1:8766${src}`)
    expect(response.headers()['content-security-policy']).toContain('sandbox allow-scripts')
    expect(response.headers()['content-security-policy']).not.toContain('allow-same-origin')
    await expect(direct.locator('#observed-label')).toHaveText('Preview mode | method: post')
    expect(await direct.evaluate(() => window.origin)).toBe('null')
    expect(await direct.evaluate(() => {
      try { void document.cookie; return false } catch (error) { return error.name === 'SecurityError' }
    })).toBe(true)
  } finally { await direct.close() }
})

test('clobber: changing fixtures clears output, old runs expire, and forged telemetry is ignored', async ({ page }) => {
  await compare(page, 'named-config')
  const oldRun = await page.getByTestId('clobber-run-id').textContent()
  const oldSrc = await page.getByTestId('clobber-fixed-result').locator('iframe').getAttribute('src')
  await page.getByTestId('clobber-fixture').selectOption('normal')
  await expect(page.getByTestId('clobber-frame')).toHaveCount(0)
  await expect(page.getByTestId('clobber-label')).toHaveCount(0)
  const { fixed } = await compare(page, 'normal')
  const run = await page.getByTestId('clobber-run-id').textContent()
  expect(run).not.toBe(oldRun)
  expect((await page.request.get(oldSrc)).status()).toBe(404)
  // These synthetic events test the dashboard's telemetry filter, not the lesson outcome.
  await page.evaluate(({ oldRun, run }) => {
    const frame = document.querySelector('[data-testid="clobber-fixed-result"] iframe')
    const evidence = { namedConfigType: 'undefined', previewPropertyType: 'undefined', formMethodType: 'String', collision: false, previewEnabled: false, method: 'post', label: 'FORGED', note: 'FORGED' }
    const data = { type: 'clobber-observation', run, mode: 'fixed', evidence }
    for (const variant of [
      { origin: location.origin, source: frame.contentWindow, data },
      { origin: 'null', source: window, data },
      { origin: 'null', source: frame.contentWindow, data: { ...data, run: oldRun } },
      { origin: 'null', source: frame.contentWindow, data: { ...data, extra: true } },
      { origin: 'null', source: frame.contentWindow, data: { ...data, evidence: { ...evidence, label: 'x'.repeat(201) } } },
      { origin: 'null', source: frame.contentWindow, data: { ...data, evidence: { ...evidence, collision: 'false' } } },
    ]) window.dispatchEvent(new MessageEvent('message', variant))
  }, { oldRun, run })
  await expect(fixed.getByTestId('clobber-label')).toHaveText('Standard view | method: post')
  await expect(fixed.getByTestId('clobber-note')).toHaveText('Hello from a scoped field')
  await page.getByTestId('nav-csp').click()
  await page.getByTestId('nav-clobber').click()
  await expect(page.getByTestId('clobber-frame')).toHaveCount(0)
  await expect(page.getByTestId('clobber-label')).toHaveCount(0)
})

test('clobber: leaving during preparation discards the delayed response and frames', async ({ page }) => {
  let release
  const paused = new Promise(resolve => { release = resolve })
  let arrived
  const pending = new Promise(resolve => { arrived = resolve })
  await page.route('**/api/clobber/prepare/', async route => {
    const response = await route.fetch()
    arrived()
    await paused
    try { await route.fulfill({ response }) } catch { /* The component aborted its request on unmount. */ }
  })
  await page.getByTestId('clobber-run').click()
  await pending
  await page.getByTestId('nav-csp').click()
  release()
  await page.getByTestId('nav-clobber').click()
  await expect(page.getByTestId('clobber-run')).toBeEnabled()
  await expect(page.getByTestId('clobber-frame')).toHaveCount(0)
  await expect(page.getByTestId('clobber-label')).toHaveCount(0)
})
