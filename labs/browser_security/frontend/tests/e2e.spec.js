import { test, expect } from '@playwright/test'

const markerPayload = (marker) => `<img src="data:image/png;base64,AA==" alt="local probe" onerror="console.log('${marker}')">`

async function startFrame(page) {
  const navigation = page.waitForEvent('framenavigated', {
    predicate: (frame) => frame.url().includes('/lab/frame/'),
  })
  await page.getByTestId('run-lab').click()
  const frame = await navigation
  await frame.waitForLoadState('load')
  await expect.poll(() => frame.evaluate(() => window.__labReady === true)).toBe(true)
  await expect(page.getByTestId('event-log')).toContainText('LAB_FRAME_READY')
  return frame
}

async function messages(frame) {
  return frame.evaluate(() => (window.__labEvents || []).map((event) => event.message))
}

async function xssFrame(page, { source = 'reflected', mode = 'off', render = 'html', payload } = {}) {
  await page.getByTestId('nav-xss').click()
  await page.getByTestId('mode-select').selectOption(mode)
  await page.getByTestId('source-select').selectOption(source)
  await page.getByTestId('render-select').selectOption(render)
  if (payload !== undefined) await page.getByTestId('payload-input').fill(payload)
  return startFrame(page)
}

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
})

for (const source of ['reflected', 'dom']) {
  test(`${source}: the raw HTML marker executes and the text control stays literal`, async ({ page }) => {
    const marker = `E2E_${source.toUpperCase()}_MARKER`
    const payload = markerPayload(marker)
    const raw = await xssFrame(page, { source, payload })
    expect(await messages(raw)).toContain(marker)
    await expect(page.getByTestId('event-log')).toContainText(marker)

    const safe = await xssFrame(page, { source, render: 'text', payload })
    expect(await messages(safe)).not.toContain(marker)
    await expect(safe.locator('body')).toContainText(payload)
    await expect(safe.locator('img[alt="local probe"]')).toHaveCount(0)
  })
}

test('an enforced CSP blocks the event handler while report-only observes execution', async ({ page }) => {
  const payload = markerPayload('E2E_POLICY_MARKER')
  const enforced = await xssFrame(page, { mode: 'self', payload })
  expect(await messages(enforced)).not.toContain('E2E_POLICY_MARKER')
  await expect.poll(() => enforced.evaluate(() => window.__labEvents.some((event) => event.details?.disposition === 'enforce'))).toBe(true)

  const observed = await xssFrame(page, { mode: 'report', payload })
  expect(await messages(observed)).toContain('E2E_POLICY_MARKER')
  await expect.poll(() => observed.evaluate(() => window.__labEvents.some((event) => event.details?.disposition === 'report'))).toBe(true)
})

for (const [fixture, marker] of [
  ['attr-double', 'XSS_TEST_ATTR_DOUBLE_06'],
  ['attr-single', 'XSS_TEST_ATTR_SINGLE_07'],
  ['attr-unquoted', 'XSS_TEST_ATTR_UNQUOTED_08'],
  ['js-single', 'XSS_TEST_JS_SINGLE_10'],
  ['js-double', 'XSS_TEST_JS_DOUBLE_11'],
  ['js-template', 'XSS_TEST_JS_TEMPLATE_12'],
  ['textarea', 'XSS_TEST_TEXTAREA_13'],
  ['title', 'XSS_TEST_TITLE_14'],
  ['script-data', 'XSS_TEST_SCRIPT_END_15'],
]) {
  test(`${fixture}: the matching parser context executes; its text control does not`, async ({ page }) => {
    await page.getByTestId('payload-select').selectOption(fixture)
    await page.getByTestId('mode-select').selectOption('off')
    await page.getByTestId('render-select').selectOption('html')
    const payload = await page.getByTestId('payload-input').inputValue()
    const raw = await startFrame(page)
    expect(await messages(raw)).toContain(marker)
    await page.getByTestId('render-select').selectOption('text')
    const safe = await startFrame(page)
    expect(await messages(safe)).not.toContain(marker)
    await expect(safe.locator('body')).toContainText(payload)
  })
}

test('a nonce does not fix injection inside an already approved JavaScript string', async ({ page }) => {
  await page.getByTestId('payload-select').selectOption('js-single')
  await page.getByTestId('mode-select').selectOption('nonce')
  await page.getByTestId('render-select').selectOption('html')
  const raw = await startFrame(page)
  expect(await messages(raw)).toContain('XSS_TEST_JS_SINGLE_10')
  await page.getByTestId('render-select').selectOption('text')
  const safe = await startFrame(page)
  expect(await messages(safe)).not.toContain('XSS_TEST_JS_SINGLE_10')
})

for (const [fixture, marker, selector] of [
  ['button', 'XSS_TEST_CLICK_05', '#sink button'],
  ['handler-string', 'XSS_TEST_HANDLER_STRING_09', '#context-action'],
]) {
  test(`${fixture}: a real click triggers the marker, and safe text has no active control`, async ({ page }) => {
    await page.getByTestId('payload-select').selectOption(fixture)
    await page.getByTestId('mode-select').selectOption('off')
    await page.getByTestId('render-select').selectOption('html')
    const payload = await page.getByTestId('payload-input').inputValue()
    const raw = await startFrame(page)
    expect(await messages(raw)).not.toContain(marker)
    await raw.locator(selector).click()
    await expect.poll(() => messages(raw)).toContain(marker)
    await expect(page.getByTestId('event-log')).toContainText(marker)
    await page.getByTestId('render-select').selectOption('text')
    const safe = await startFrame(page)
    expect(await messages(safe)).not.toContain(marker)
    await expect(safe.locator('#sink')).toContainText(payload)
    await expect(safe.locator('#sink button, #sink a')).toHaveCount(0)
  })
}

test('URL context preserves the link but Chromium does not execute it in this opaque-origin lab', async ({ page, browserName }) => {
  test.skip(browserName !== 'chromium', 'This assertion records the observed Chromium sandbox behavior, not a cross-browser CSP guarantee.')
  await page.getByTestId('payload-select').selectOption('url')
  await page.getByTestId('mode-select').selectOption('off')
  await page.getByTestId('render-select').selectOption('html')
  const payload = await page.getByTestId('payload-input').inputValue()
  const raw = await startFrame(page)
  expect(await raw.evaluate(() => window.origin)).toBe('null')
  await expect(raw.locator('#context-action')).toHaveAttribute('href', payload)
  // This listener only acknowledges the real click. It does not evaluate the
  // URL or disable CSP; execution is observed through the page's own markers.
  await raw.locator('#context-action').evaluate((link) => {
    link.addEventListener('click', () => { window.__urlClickDelivered = true }, { once: true })
  })
  await raw.locator('#context-action').click()
  await expect.poll(() => raw.evaluate(() => window.__urlClickDelivered === true)).toBe(true)
  await raw.evaluate(() => new Promise((resolve) => setTimeout(resolve, 100)))
  expect(await messages(raw)).not.toContain('XSS_TEST_URL_16')
  await page.getByTestId('render-select').selectOption('text')
  const safe = await startFrame(page)
  await expect(safe.locator('#sink')).toContainText(payload)
  await expect(safe.locator('#sink a')).toHaveCount(0)
})

const baselineCases = [
  { mode: 'off', nonce: true, wrong: true, hashCount: 2, external: true },
  { mode: 'self', nonce: false, wrong: false, hashCount: 0, external: true },
  { mode: 'nonce', nonce: true, wrong: false, hashCount: 0, external: false },
  { mode: 'hash', nonce: false, wrong: false, hashCount: 1, external: false },
  { mode: 'dynamic', nonce: true, wrong: false, hashCount: 0, external: false },
  { mode: 'report', nonce: true, wrong: true, hashCount: 2, external: true },
  { mode: 'tt', nonce: true, wrong: false, hashCount: 0, external: false },
]

for (const entry of baselineCases) {
  test(`CSP ${entry.mode}: browser enforces the nonce, exact hash, and parser-script controls`, async ({ page }) => {
    await page.getByTestId('nav-csp').click()
    await page.getByTestId('mode-select').selectOption(entry.mode)
    await page.getByTestId('probe-select').selectOption('callback')
    const frame = await startFrame(page)
    const observed = await messages(frame)
    expect(observed).toContain('CSP_BOOT_OK')
    expect(observed.includes('CSP_NONCE_MATCH')).toBe(entry.nonce)
    expect(observed.includes('CSP_NONCE_WRONG')).toBe(entry.wrong)
    expect(observed.filter((message) => message === 'CSP_HASH_EXACT')).toHaveLength(entry.hashCount)
    expect(observed.includes('CSP_PARSER_EXTERNAL')).toBe(entry.external)
    expect(observed).toContain('CSP_CALLBACK_TIMER')
  })
}

for (const [mode, loading, executes] of [
  ['self', 'parser', true],
  ['nonce', 'parser', false],
  ['dynamic', 'parser', false],
  ['dynamic', 'trusted', true],
  ['nonce', 'trusted', false],
]) {
  test(`JSONP ${mode}, ${loading}: callback execution is ${executes ? 'allowed' : 'blocked'}`, async ({ page }) => {
    await page.getByTestId('nav-jsonp').click()
    await page.getByTestId('mode-select').selectOption(mode)
    await page.getByTestId('jsonp-loading-select').selectOption(loading)
    const frame = await startFrame(page)
    expect((await messages(frame)).includes('JSONP_TEST_22')).toBe(executes)
  })
}

test('Trusted Types rejects the DOM string sink when supported by this browser', async ({ page }) => {
  const supported = await page.evaluate(() => 'trustedTypes' in window)
  test.skip(!supported, 'This browser does not expose the Trusted Types API; nonce CSP coverage is tested separately.')
  const frame = await xssFrame(page, { source: 'dom', mode: 'tt', payload: markerPayload('E2E_TT_MARKER') })
  expect(await messages(frame)).not.toContain('E2E_TT_MARKER')
  await expect(frame.locator('img[alt="local probe"]')).toHaveCount(0)
  const events = await frame.evaluate(() => window.__labEvents)
  expect(JSON.stringify(events)).toMatch(/TrustedHTML|Trusted Type|trusted-types|TypeError/)
})

test('saved Django data executes only in the selected raw exercise and can be cleared', async ({ page }) => {
  const payload = markerPayload('E2E_STORED_MARKER')
  await page.getByTestId('payload-input').fill(payload)
  await page.getByTestId('stored-save').click()
  await expect.poll(async () => (await (await page.request.get('/api/bootstrap')).json()).stored?.payload).toBe(payload)
  await page.reload()
  await expect(page.getByTestId('app-ready')).toBeVisible()
  const raw = await xssFrame(page, { source: 'stored' })
  expect(await messages(raw)).toContain('E2E_STORED_MARKER')
  const safe = await xssFrame(page, { source: 'stored', render: 'text' })
  expect(await messages(safe)).not.toContain('E2E_STORED_MARKER')
  await expect(safe.locator('body')).toContainText(payload)
  await page.getByTestId('stored-clear').click()
  await expect.poll(async () => JSON.stringify((await (await page.request.get('/api/bootstrap')).json()).stored)).not.toContain('E2E_STORED_MARKER')
})

test('exercise frames cannot read the Vue parent, and unrelated messages are ignored', async ({ page }) => {
  const payload = `<img src="data:image/png;base64,AA==" onerror="try { parent.document.body; console.log('ISOLATION_FAILED') } catch { console.log('ISOLATION_OK') }">`
  const frame = await xssFrame(page, { payload })
  expect(await messages(frame)).toContain('ISOLATION_OK')
  expect(await messages(frame)).not.toContain('ISOLATION_FAILED')
  await expect(page.getByTestId('lab-frame')).toHaveAttribute('sandbox', 'allow-scripts')
  const runId = new URL(frame.url()).searchParams.get('run_id')
  // Send a matching envelope from the wrong window; this exercises the real receiver.
  await page.evaluate((id) => new Promise((resolve) => {
    const delivered = (event) => {
      if (event.source !== window || event.data?.message !== 'FORGED_PARENT_MESSAGE') return
      window.removeEventListener('message', delivered)
      setTimeout(resolve, 0)
    }
    window.addEventListener('message', delivered)
    window.postMessage({ channel: 'browser-security-lab', runId: id, kind: 'marker', message: 'FORGED_PARENT_MESSAGE' }, '*')
  }), runId)
  await expect(page.getByTestId('event-log')).not.toContainText('FORGED_PARENT_MESSAGE')
})

test('HTML uploads have safe and isolated active previews, then delete cleanly', async ({ page }) => {
  await page.getByTestId('nav-uploads').click()
  await page.getByTestId('upload-policy').selectOption('lab')
  const name = '<img data-marker=UPLOAD_FILENAME_TEST>.html'
  const content = '<!doctype html><p>UPLOAD_BODY_TEST</p><script>document.body.dataset.uploadMarker="executed"</script>'
  await page.getByTestId('upload-input').setInputFiles({ name, mimeType: 'text/html', buffer: Buffer.from(content) })
  await page.getByTestId('upload-submit').click()
  await expect(page.getByTestId('upload-list')).toContainText('UPLOAD_FILENAME_TEST')
  const records = (await (await page.request.get('/api/uploads/')).json()).uploads
  expect(records).toHaveLength(1)
  const record = records[0]
  await expect(page.getByTestId('upload-list').locator('img[data-marker="UPLOAD_FILENAME_TEST"]')).toHaveCount(0)

  await page.getByTestId(`upload-preview-${record.id}`).click()
  const safe = page.frameLocator('[data-testid="upload-preview-frame"]')
  await expect(safe.locator('body')).toContainText('UPLOAD_BODY_TEST')
  await expect(safe.locator('body')).not.toHaveAttribute('data-upload-marker', 'executed')

  await page.getByTestId(`upload-active-preview-${record.id}`).click()
  const active = page.frameLocator('[data-testid="upload-preview-frame"]')
  await expect(active.locator('body')).toHaveAttribute('data-upload-marker', 'executed')
  const response = await page.request.get(record.activePreviewUrl)
  expect(response.headers()['content-security-policy']).toContain('sandbox allow-scripts')
  expect(response.headers()['content-security-policy']).not.toContain('allow-same-origin')
  const download = await page.request.get(record.downloadUrl)
  expect(download.headers()['content-disposition']).toContain('attachment')
  expect(download.headers()['x-content-type-options']).toBe('nosniff')

  await page.getByTestId(`upload-delete-${record.id}`).click()
  await expect.poll(async () => (await (await page.request.get('/api/uploads/')).json()).uploads.length).toBe(0)
  expect((await page.request.get(record.downloadUrl)).status()).toBe(404)
})

test('the built UI and standard probe contact only this loopback server or data URLs', async ({ page }) => {
  const external = []
  page.on('request', (request) => {
    const url = new URL(request.url())
    if (!['data:', 'about:', 'blob:'].includes(url.protocol) && url.origin !== 'http://127.0.0.1:8766') external.push(request.url())
  })
  await page.reload()
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await xssFrame(page, { payload: markerPayload('E2E_LOCAL_MARKER') })
  expect(external).toEqual([])
})
