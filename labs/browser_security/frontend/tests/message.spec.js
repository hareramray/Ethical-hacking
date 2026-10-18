import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-message').click()
  await expect(page.getByTestId('message-run')).toBeEnabled()
})

async function compare(page, fixture) {
  await page.getByTestId('message-fixture').selectOption(fixture)
  await page.getByTestId('message-run').click()
  const vulnerable = page.getByTestId('message-vulnerable-result')
  const fixed = page.getByTestId('message-fixed-result')
  await expect(vulnerable.locator('.traversal-outcome')).toBeVisible()
  await expect(fixed.locator('.traversal-outcome')).toBeVisible()
  await expect(page.getByTestId('message-run')).toBeEnabled()
  return { vulnerable, fixed }
}

test('message: trusted plain text is accepted by both actual receiver windows', async ({ page }) => {
  const results = await compare(page, 'normal')
  const mainOrigin = new URL(page.url()).origin
  for (const result of Object.values(results)) {
    await expect(result.locator('.traversal-outcome')).toHaveText('accepted')
    await expect(result.getByTestId('message-origin')).toHaveText(mainOrigin)
    await expect(result.getByTestId('message-source')).toHaveText('Matches')
    await expect(result.getByTestId('message-schema')).toHaveText('Yes')
    await expect(result.getByTestId('message-marker')).toHaveText('No')
    await expect(result.getByTestId('message-rendered')).toHaveText('Hello from the authorized message fixture.')
  }
  for (const mode of ['vulnerable', 'fixed']) {
    const receiver = page.frameLocator(`[data-testid="message-${mode}-frame"]`)
    await expect(receiver.locator('#senders iframe')).toHaveCount(1)
    await expect(receiver.locator('#output')).toHaveText('Hello from the authorized message fixture.')
  }
})

test('message: correct window on the wrong origin is rejected by the fixed receiver', async ({ page }) => {
  const { vulnerable, fixed } = await compare(page, 'wrong-origin')
  const peerOrigin = new URL(await page.getByTestId('message-fixed-frame').getAttribute('src')).origin
  for (const result of [vulnerable, fixed]) {
    await expect(result.getByTestId('message-origin')).toHaveText(peerOrigin)
    await expect(result.getByTestId('message-source')).toHaveText('Matches')
    await expect(result.getByTestId('message-schema')).toHaveText('Yes')
  }
  await expect(vulnerable.locator('.traversal-outcome')).toHaveText('accepted')
  await expect(vulnerable.getByTestId('message-rendered')).toHaveText('WRONG_ORIGIN_MARKER')
  await expect(fixed.locator('.traversal-outcome')).toHaveText('rejected')
  await expect(fixed.getByTestId('message-rendered')).toHaveText('(empty)')
})

test('message: a second window on the trusted origin does not gain authority', async ({ page }) => {
  const { vulnerable, fixed } = await compare(page, 'wrong-source')
  for (const result of [vulnerable, fixed]) {
    await expect(result.getByTestId('message-origin')).toHaveText(new URL(page.url()).origin)
    await expect(result.getByTestId('message-source')).toHaveText('Does not match')
    await expect(result.getByTestId('message-schema')).toHaveText('Yes')
  }
  await expect(vulnerable.getByTestId('message-rendered')).toHaveText('WRONG_WINDOW_MARKER')
  await expect(fixed.locator('.traversal-outcome')).toHaveText('rejected')
  await expect(fixed.getByTestId('message-rendered')).toHaveText('(empty)')
  await expect(page.frameLocator('[data-testid="message-fixed-frame"]').locator('#senders iframe')).toHaveCount(2)
})

test('message: trusted sender still needs a strict message schema', async ({ page }) => {
  const { vulnerable, fixed } = await compare(page, 'wrong-shape')
  for (const result of [vulnerable, fixed]) {
    await expect(result.getByTestId('message-source')).toHaveText('Matches')
    await expect(result.getByTestId('message-origin')).toHaveText(new URL(page.url()).origin)
    await expect(result.getByTestId('message-schema')).toHaveText('No')
  }
  await expect(vulnerable.getByTestId('message-rendered')).toHaveText('WRONG_SHAPE_MARKER')
  await expect(fixed.locator('.traversal-outcome')).toHaveText('rejected')
  await expect(fixed.getByTestId('message-rendered')).toHaveText('(empty)')
})

test('message: accepted markup executes only inside the vulnerable peer receiver', async ({ page }) => {
  const externalRequests = []
  page.on('request', request => {
    const url = new URL(request.url())
    if (['http:', 'https:'].includes(url.protocol) && url.hostname !== '127.0.0.1') externalRequests.push(url.href)
  })
  const { vulnerable, fixed } = await compare(page, 'markup')
  for (const result of [vulnerable, fixed]) {
    await expect(result.locator('.traversal-outcome')).toHaveText('accepted')
    await expect(result.getByTestId('message-schema')).toHaveText('Yes')
  }
  await expect(vulnerable.getByTestId('message-marker')).toHaveText('Yes')
  await expect(vulnerable.getByTestId('message-rendered')).toHaveText('MESSAGE_HTML_MARKER')
  await expect(fixed.getByTestId('message-marker')).toHaveText('No')
  await expect(fixed.getByTestId('message-rendered')).toContainText('<img src="data:image/png;base64,AA=="')
  await expect(page.frameLocator('[data-testid="message-vulnerable-frame"]').locator('#output img')).toHaveCount(1)
  await expect(page.frameLocator('[data-testid="message-fixed-frame"]').locator('#output img')).toHaveCount(0)
  expect(await page.evaluate(() => window.__messageMarker)).toBeUndefined()
  expect(externalRequests).toEqual([])
  // The peer origin serves lesson documents, not the dashboard's data APIs.
  const peerOrigin = new URL(await page.getByTestId('message-fixed-frame').getAttribute('src')).origin
  const response = await page.request.get(peerOrigin + '/api/bootstrap')
  expect(response.status()).toBe(404)
})

test('message: stale runs and a mismatched telemetry window cannot populate dashboard evidence', async ({ page }) => {
  let releaseScripts
  const gate = new Promise(resolve => { releaseScripts = resolve })
  await page.route('**/peer/message/receiver.js', async route => { await gate; await route.continue() })
  await page.getByTestId('message-run').click()
  await expect(page.getByTestId('message-fixed-frame')).toHaveCount(1)
  await expect(page.getByTestId('message-vulnerable-frame')).toHaveCount(1)
  const fixedUrl = await page.getByTestId('message-fixed-frame').getAttribute('src')
  let fixedFrame
  await expect.poll(() => { fixedFrame = page.frames().find(frame => frame.url() === fixedUrl); return !!fixedFrame }).toBe(true)
  await fixedFrame.locator('body').waitFor({ state: 'attached' })
  const forged = await fixedFrame.evaluate(async () => {
    const config = JSON.parse(document.body.dataset.config)
    const result = {outcome: 'accepted', observedOrigin: config.mainOrigin, expectedOrigin: config.mainOrigin,
      sourceMatch: true, schemaValid: true, accepted: true, renderedText: 'FORGED_RESULT', markerObserved: false, reason: 'Forged telemetry'}
    // These are real browser messages. One has a stale run; one claims the other frame's mode.
    parent.postMessage({channel: 'message-lesson-result', runId: 'z'.repeat(24), fixture: config.fixture, mode: 'fixed', result}, config.mainOrigin)
    parent.postMessage({channel: 'message-lesson-result', runId: config.runId, fixture: config.fixture, mode: 'vulnerable', result}, config.mainOrigin)
    const envelope = {channel: 'message-lesson-result', runId: config.runId, fixture: config.fixture, mode: 'fixed', result}
    parent.postMessage({...envelope, extra: true}, config.mainOrigin)
    parent.postMessage({...envelope, result: {...result, extra: true}}, config.mainOrigin)
    parent.postMessage({...envelope, result: {...result, observedOrigin: 'https://example.invalid'}}, config.mainOrigin)
    parent.postMessage({...envelope, result: {...result, outcome: 'rejected'}}, config.mainOrigin)
    await new Promise(resolve => setTimeout(resolve, 100))
    return true
  })
  expect(forged).toBe(true)
  await expect(page.locator('[data-testid^="message-"] .traversal-outcome')).toHaveCount(0)
  await expect(page.getByText('FORGED_RESULT')).toHaveCount(0)
  releaseScripts()
  await expect(page.getByTestId('message-run')).toBeEnabled()
  for (const mode of ['vulnerable', 'fixed']) {
    await expect(page.getByTestId(`message-${mode}-result`).getByTestId('message-rendered')).toHaveText('Hello from the authorized message fixture.')
  }
  await page.getByTestId('nav-xss').click()
  await expect(page.locator('[data-testid$="-frame"][data-testid^="message-"]')).toHaveCount(0)
})
