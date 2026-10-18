import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-oauth').click()
  await expect(page.getByTestId('oauth-run')).toBeEnabled()
})

async function compare(page, fixture) {
  await page.getByTestId('oauth-fixture').selectOption(fixture)
  const trace = []
  const record = response => {
    const url = new URL(response.url())
    if (url.pathname.startsWith('/lab/oauth/')) trace.push({ url, status: response.status(), headers: response.headers() })
  }
  page.on('response', record)
  await page.getByTestId('oauth-run').click()
  for (const mode of ['vulnerable', 'fixed']) {
    await expect(page.getByTestId(`oauth-${mode}-result`).locator('.traversal-outcome')).toBeVisible()
  }
  await expect(page.getByTestId('oauth-run')).toBeEnabled()
  page.off('response', record)
  return { trace, panel: mode => page.getByTestId(`oauth-${mode}-result`) }
}

test('oauth: valid control performs real browser authorization redirects and both clients accept', async ({ page }) => {
  const { trace, panel } = await compare(page, 'valid')
  for (const mode of ['vulnerable', 'fixed']) {
    await expect(panel(mode).getByTestId('oauth-marker')).toHaveText('FICTIONAL_READER_ACCEPTED')
    await expect(panel(mode).getByTestId('oauth-statuses')).toHaveText('200')
    const chain = trace.filter(item => item.url.searchParams.get('mode') === mode)
    expect(chain.map(item => item.url.pathname)).toEqual(['/lab/oauth/start/', '/lab/oauth/provider/authorize/', '/lab/oauth/callback/'])
    expect(chain.map(item => item.status)).toEqual([302, 302, 200])
    expect(chain[1].url.searchParams.get('code_challenge_method')).toBe('S256')
    expect(chain[2].url.searchParams.get('code')).toBeTruthy()
    expect(chain[2].headers['content-security-policy']).toContain('sandbox allow-scripts')
    expect(chain[2].headers['cache-control']).toBe('no-store')
    expect(await page.getByTestId(`oauth-${mode}-frame`).getAttribute('sandbox')).toBe('allow-scripts')
    await expect(page.frameLocator(`[data-testid="oauth-${mode}-frame"]`).locator('#marker')).toHaveText('FICTIONAL_READER_ACCEPTED')
  }
  expect(trace.some(item => item.url.pathname.endsWith('/token/'))).toBe(false)
})

for (const [fixture, boundary, statuses] of [
  ['wrong-verifier', 'Provider code exchange', '400'],
  ['state-mismatch', 'Client state', 'No token exchange'],
  ['nonce-mismatch', 'Client ID-token validation', '200'],
]) {
  test(`oauth: ${fixture} refuses at ${boundary} while the vulnerable comparison accepts`, async ({ page }) => {
    const { panel } = await compare(page, fixture)
    await expect(panel('vulnerable').locator('.traversal-outcome')).toHaveText('accepted')
    await expect(panel('vulnerable').getByTestId('oauth-statuses')).toHaveText('200')
    await expect(panel('fixed').locator('.traversal-outcome')).toHaveText('rejected')
    await expect(panel('fixed').getByTestId('oauth-boundary')).toHaveText(boundary)
    await expect(panel('fixed').getByTestId('oauth-statuses')).toHaveText(statuses)
    await expect(page.frameLocator('[data-testid="oauth-fixed-frame"]').locator('#marker')).toHaveText('OAUTH_REFUSED')
  })
}

test('oauth: code replay preserves the first successful exchange and refuses the second', async ({ page }) => {
  const { panel } = await compare(page, 'reused-code')
  await expect(panel('vulnerable').getByTestId('oauth-statuses')).toHaveText('200 → 200')
  await expect(panel('vulnerable').getByTestId('oauth-marker')).toHaveText('REUSED_CODE_ACCEPTED')
  await expect(panel('fixed').getByTestId('oauth-statuses')).toHaveText('200 → 400')
  await expect(panel('fixed').getByTestId('oauth-marker')).toHaveText('FIRST_LOGIN_OK_REPLAY_REFUSED')
})

test('oauth: invalid callback reaches an owned alternate only with permissive provider registration', async ({ page }) => {
  const { trace, panel } = await compare(page, 'invalid-redirect')
  await expect(panel('vulnerable').getByTestId('oauth-marker')).toHaveText('ALTERNATE_CALLBACK_CODE_MARKER')
  await expect(panel('fixed').getByTestId('oauth-boundary')).toHaveText('Provider redirect URI')
  for (const mode of ['vulnerable', 'fixed']) await expect(panel(mode).getByTestId('oauth-statuses')).toHaveText('No token exchange')
  const fixed = trace.filter(item => item.url.searchParams.get('mode') === 'fixed')
  expect(fixed.map(item => item.url.pathname)).toEqual(['/lab/oauth/start/', '/lab/oauth/provider/authorize/'])
  expect(fixed.map(item => item.status)).toEqual([302, 200])
  const alternate = trace.find(item => item.url.pathname === '/lab/oauth/alternate-callback/')
  expect(alternate.url.searchParams.get('code')).toBeTruthy()
  expect(alternate.url.origin).toBe(new URL(page.url()).origin)
})

test('oauth: stale, wrong-source and malformed result messages cannot overwrite a completed run', async ({ page }) => {
  const { panel, trace } = await compare(page, 'valid')
  const run = trace[0].url.searchParams.get('run')
  const frame = page.frames().find(item => item.url().includes('/lab/oauth/callback/') && new URL(item.url()).searchParams.get('mode') === 'fixed')
  const content = { channel: 'oauth-lesson-result', runId: run, fixture: 'valid', mode: 'fixed',
    evidence: { outcome: 'accepted', boundary: 'Client identity', detail: 'forged', marker: 'FICTIONAL_READER_ACCEPTED', tokenStatuses: [200], steps: [] } }
  await page.evaluate(data => window.postMessage(data, location.origin), content)
  await expect(panel('fixed').getByTestId('oauth-detail')).not.toHaveText('forged')
  await frame.evaluate(({ data, origin }) => {
    parent.postMessage({ ...data, runId: 'a'.repeat(24) }, origin)
    parent.postMessage({ ...data, evidence: { ...data.evidence, tokenStatuses: ['200'] } }, origin)
    parent.postMessage({ ...data, extra: true }, origin)
  }, { data: content, origin: new URL(page.url()).origin })
  await expect(panel('fixed').getByTestId('oauth-detail')).not.toHaveText('forged')
  const next = await compare(page, 'wrong-verifier')
  expect(next.trace[0].url.searchParams.get('run')).not.toBe(run)
  expect(page.frames().some(item => item.url().includes(`run=${run}`))).toBe(false)
})

test('oauth: leaving during preparation does not create delayed authorization frames', async ({ page }) => {
  let release, started
  const held = new Promise(resolve => { release = resolve })
  const intercepted = new Promise(resolve => { started = resolve })
  await page.route('**/api/oauth/prepare/', async route => {
    const response = await route.fetch()
    started()
    await held
    await route.fulfill({ response }).catch(() => {})
  })
  await page.getByTestId('oauth-run').click()
  await intercepted
  await page.getByTestId('nav-csp').click()
  release()
  await expect(page.getByTestId('oauth-fixed-frame')).toHaveCount(0)
  await page.getByTestId('nav-oauth').click()
  await expect(page.getByTestId('oauth-run')).toBeEnabled()
  await expect(page.getByTestId('oauth-fixed-frame')).toHaveCount(0)
})
