import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-worker').click()
  await expect(page.getByTestId('worker-run')).toBeEnabled()
})

async function run(page, fixture) {
  await page.getByTestId('worker-fixture').selectOption(fixture)
  await page.getByTestId('worker-run').click()
  const control = page.getByTestId('worker-control-result')
  const experiment = page.getByTestId('worker-experiment-result')
  await expect(control.getByTestId('worker-status')).toHaveText('executed')
  await expect(control.getByTestId('worker-marker')).toHaveText('HARMLESS_WORKER_MARKER')
  await expect(control.frameLocator('iframe').locator('#worker-status')).toHaveText('HARMLESS_WORKER_MARKER')
  return { control, experiment }
}

test('worker: explicit allow executes both real dedicated workers without a policy violation', async ({ page }) => {
  const policyResponse = page.waitForResponse(response => response.url().includes('/lab/worker/frame/') && response.url().includes('mode=experiment'))
  const { control, experiment } = await run(page, 'allow')
  await expect(experiment.getByTestId('worker-status')).toHaveText('executed')
  await expect(experiment.getByTestId('worker-marker')).toHaveText('HARMLESS_WORKER_MARKER')
  await expect(experiment.frameLocator('iframe').locator('#worker-status')).toHaveText('HARMLESS_WORKER_MARKER')
  await expect(page.getByTestId('worker-delivery')).toContainText('Both workers finished')
  for (const result of [control, experiment]) {
    await expect(result.getByTestId('worker-report-count')).toHaveText('0')
    await expect(result.getByTestId('worker-events')).toHaveText('No local worker-src event observed')
  }
  const headers = (await policyResponse).headers()
  expect(headers['content-security-policy']).toContain("worker-src 'self'")
  expect(headers['content-security-policy-report-only']).toBeUndefined()
})

for (const [fixture, disposition, status] of [['enforce', 'enforce', 'error'], ['report', 'report', 'executed']]) {
  test(`worker: ${fixture} generates an actual HTTP report independently of the local event`, async ({ page }) => {
    const policyResponse = page.waitForResponse(response => response.url().includes('/lab/worker/frame/') && response.url().includes('mode=experiment'))
    // Observe the browser's own CSP POST. The test never manufactures a report.
    const receipt = page.waitForResponse(response => response.url().includes('/api/worker/report/') && response.request().method() === 'POST', { timeout: 12000 })
    const { control, experiment } = await run(page, fixture)
    await expect(experiment.getByTestId('worker-status')).toHaveText(status)
    await expect(experiment.getByTestId('worker-events')).toContainText(`worker-src: ${disposition}`)
    const received = await receipt
    expect(received.status()).toBe(204)
    expect(received.request().headers()['content-type']).toContain('application/csp-report')
    const browserReport = received.request().postDataJSON()['csp-report']
    expect(browserReport['effective-directive']).toBe('worker-src')
    expect(browserReport.disposition).toBe(disposition)
    await expect.poll(async () => Number(await experiment.getByTestId('worker-report-count').textContent())).toBeGreaterThan(0)
    await expect(experiment.getByTestId('worker-report').first()).toContainText(`worker-src / ${disposition} / /lab/worker/marker.js`)
    await expect(control.getByTestId('worker-report-count')).toHaveText('0')
    await expect(page.getByTestId('worker-delivery')).toContainText('Django accepted an HTTP violation report')
    const headers = (await policyResponse).headers()
    if (fixture === 'enforce') {
      expect(headers['content-security-policy']).toContain("worker-src 'none'")
      expect(headers['content-security-policy-report-only']).toBeUndefined()
      await expect(experiment.getByTestId('worker-marker')).toHaveText('No marker received')
      await expect(experiment.frameLocator('iframe').locator('#worker-status')).toHaveText('error')
    } else {
      expect(headers['content-security-policy']).toContain("worker-src 'self'")
      expect(headers['content-security-policy-report-only']).toContain("worker-src 'none'")
      await expect(experiment.getByTestId('worker-marker')).toHaveText('HARMLESS_WORKER_MARKER')
      await expect(experiment.frameLocator('iframe').locator('#worker-status')).toHaveText('HARMLESS_WORKER_MARKER')
    }
  })
}

test('worker: session isolation, fresh runs, and source-bound telemetry', async ({ page, browser }) => {
  const { experiment } = await run(page, 'allow')
  await expect(experiment.getByTestId('worker-status')).toHaveText('executed')
  await expect(page.getByTestId('worker-delivery')).toBeVisible()
  const oldRun = await page.getByTestId('worker-run-id').textContent()
  const oldSrc = await experiment.locator('iframe').getAttribute('src')
  const other = await browser.newContext()
  try {
    expect((await other.request.get(`http://127.0.0.1:8766${oldSrc}`)).status()).toBe(404)
    expect((await other.request.get(`http://127.0.0.1:8766/api/worker/state/?run=${oldRun}`)).status()).toBe(404)
  } finally { await other.close() }
  await page.evaluate(run => {
    const frame = document.querySelector('[data-testid="worker-experiment-result"] iframe')
    const data = { type: 'worker-observation', run, mode: 'experiment', evidence: { status: 'error', marker: '', errors: 1, events: [{directive:'worker-src',disposition:'enforce'}] } }
    for (const variant of [
      { origin: 'null', source: frame.contentWindow, data },
      { origin: location.origin, source: window, data },
      { origin: location.origin, source: frame.contentWindow, data: { ...data, run: '0'.repeat(32) } },
      { origin: location.origin, source: frame.contentWindow, data: { ...data, extra: true } },
      { origin: location.origin, source: frame.contentWindow, data: { ...data, evidence: { ...data.evidence, events: [{ directive:'script-src', disposition:'enforce' }] } } },
    ]) window.dispatchEvent(new MessageEvent('message', variant))
  }, oldRun)
  await expect(experiment.getByTestId('worker-status')).toHaveText('executed')
  await expect(experiment.getByTestId('worker-report-count')).toHaveText('0')
  await page.getByTestId('worker-fixture').selectOption('report')
  await expect(page.getByTestId('worker-frame')).toHaveCount(0)
  await run(page, 'allow')
  expect(await page.getByTestId('worker-run-id').textContent()).not.toBe(oldRun)
  expect((await page.request.get(oldSrc)).status()).toBe(404)
  await page.getByTestId('nav-csp').click()
  await page.getByTestId('nav-worker').click()
  await expect(page.getByTestId('worker-frame')).toHaveCount(0)
})

test('worker: leaving during preparation discards delayed frames and collector polling', async ({ page }) => {
  let release, arrived
  const paused = new Promise(resolve => { release = resolve })
  const pending = new Promise(resolve => { arrived = resolve })
  await page.route('**/api/worker/prepare/', async route => {
    const response = await route.fetch()
    arrived()
    await paused
    try { await route.fulfill({ response }) } catch { /* Aborted when the component left. */ }
  })
  await page.getByTestId('worker-run').click()
  await pending
  await page.getByTestId('nav-csp').click()
  release()
  await page.getByTestId('nav-worker').click()
  await expect(page.getByTestId('worker-run')).toBeEnabled()
  await expect(page.getByTestId('worker-frame')).toHaveCount(0)
  await expect(page.getByTestId('worker-polling')).toHaveCount(0)
})
