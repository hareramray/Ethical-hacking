import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-sanitizer').click()
  await expect(page.getByTestId('sanitizer-run')).toBeEnabled()
})

async function save(page, fixture) {
  await page.getByTestId('sanitizer-fixture').selectOption(fixture)
  await page.getByTestId('sanitizer-run').click()
  const vulnerable = page.getByTestId('sanitizer-vulnerable-result')
  const fixed = page.getByTestId('sanitizer-fixed-result')
  await expect(vulnerable.getByTestId('sanitizer-marker-count')).toBeVisible()
  await expect(fixed.getByTestId('sanitizer-marker-count')).toBeVisible()
  await expect(page.getByTestId('sanitizer-run')).toBeEnabled()
  return { vulnerable, fixed }
}

test('sanitizer: Markdown formatting survives and encoded markup stays text', async ({ page }) => {
  let results = await save(page, 'normal')
  for (const result of Object.values(results)) {
    await expect(result.getByTestId('sanitizer-marker-count')).toHaveText('0')
    await expect(result.getByTestId('sanitizer-formatting')).toHaveText('1 / 1')
    const frame = result.frameLocator('iframe')
    await expect(frame.locator('#saved-content strong')).toHaveText('Bold stays')
    await expect(frame.locator('#saved-content em')).toHaveText('emphasis stays')
    await expect(frame.locator('#saved-content li')).toHaveCount(2)
    await expect(frame.locator('#saved-content code')).toHaveText('<tag> stays text')
  }
  results = await save(page, 'encoded')
  for (const result of Object.values(results)) {
    await expect(result.getByTestId('sanitizer-marker-count')).toHaveText('0')
    await expect(result.getByTestId('sanitizer-image-count')).toHaveText('0')
    await expect(result.frameLocator('iframe').locator('#saved-content')).toContainText('<img src=')
    await expect(result.frameLocator('iframe').locator('#saved-content img')).toHaveCount(0)
  }
})

test('sanitizer: actual image-error execution is removed from Markdown and rich HTML', async ({ page }) => {
  for (const fixture of ['markdown-html', 'rich-html']) {
    const { vulnerable, fixed } = await save(page, fixture)
    await expect(vulnerable.getByTestId('sanitizer-marker-count')).toHaveText('1')
    await expect(vulnerable.getByTestId('sanitizer-event-count')).toHaveText('1')
    await expect(fixed.getByTestId('sanitizer-marker-count')).toHaveText('0')
    await expect(fixed.getByTestId('sanitizer-event-count')).toHaveText('0')
    await expect(fixed.getByTestId('sanitizer-formatting')).toHaveText('1 / 1')
    await expect(vulnerable.frameLocator('iframe').locator('#saved-content img')).toHaveAttribute('onerror', 'window.sanitizerMark()')
    await expect(fixed.frameLocator('iframe').locator('#saved-content img')).not.toHaveAttribute('onerror')
    await expect(fixed.frameLocator('iframe').locator('#saved-content img')).not.toHaveAttribute('src')
  }
  await expect(page.locator('#saved-content')).toHaveCount(0)
  expect(await page.evaluate(() => typeof window.sanitizerMark)).toBe('undefined')
})

test('sanitizer: stored pair survives refresh, stays session-isolated, and direct previews remain sandboxed', async ({ page, browser }) => {
  await save(page, 'rich-html')
  const run = await page.getByTestId('sanitizer-run-id').textContent()
  const src = await page.getByTestId('sanitizer-vulnerable-result').locator('iframe').getAttribute('src')
  await page.reload()
  await page.getByTestId('nav-sanitizer').click()
  await expect(page.getByTestId('sanitizer-run-id')).toHaveText(run)
  await expect(page.getByTestId('sanitizer-vulnerable-result').getByTestId('sanitizer-marker-count')).toHaveText('1')
  await expect(page.getByTestId('sanitizer-fixed-result').getByTestId('sanitizer-marker-count')).toHaveText('0')
  const other = await browser.newContext()
  try {
    const state = await other.request.get('http://127.0.0.1:8766/api/sanitizer/state/')
    expect(await state.json()).toEqual({ saved: null })
    expect((await other.request.get(`http://127.0.0.1:8766${src}`)).status()).toBe(404)
  } finally { await other.close() }
  const direct = await page.context().newPage()
  try {
    const response = await direct.goto(`http://127.0.0.1:8766${src}`)
    expect(response.headers()['content-security-policy']).toContain('sandbox allow-scripts')
    await expect(direct.locator('#observation')).toHaveText('Marker executions observed: 1')
    expect(await direct.evaluate(() => window.origin)).toBe('null')
    expect(await direct.evaluate(() => {
      try { void document.cookie; return false } catch (error) { return error.name === 'SecurityError' }
    })).toBe(true)
  } finally { await direct.close() }
})

test('sanitizer: replacing a save invalidates old frames and ignores forged or stale telemetry', async ({ page }) => {
  await save(page, 'rich-html')
  const oldRun = await page.getByTestId('sanitizer-run-id').textContent()
  const oldSrc = await page.getByTestId('sanitizer-vulnerable-result').locator('iframe').getAttribute('src')
  const { fixed } = await save(page, 'normal')
  const newRun = await page.getByTestId('sanitizer-run-id').textContent()
  expect(newRun).not.toBe(oldRun)
  expect((await page.request.get(oldSrc)).status()).toBe(404)
  await page.evaluate(({ oldRun, newRun }) => {
    const evidence = { markerCount: 9, strongCount: 0, emphasisCount: 0, imageCount: 0, eventAttributeCount: 0, text: 'FORGED' }
    const frame = document.querySelector('[data-testid="sanitizer-fixed-result"] iframe')
    for (const [origin, source, run] of [
      [location.origin, frame.contentWindow, newRun],
      ['null', window, newRun],
      ['null', frame.contentWindow, oldRun],
    ]) window.dispatchEvent(new MessageEvent('message', { origin, source, data: { type: 'sanitizer-observation', run, mode: 'fixed', evidence } }))
  }, { oldRun, newRun })
  await expect(fixed.getByTestId('sanitizer-marker-count')).toHaveText('0')
  await expect(fixed.getByTestId('sanitizer-formatting')).toHaveText('1 / 1')
})
