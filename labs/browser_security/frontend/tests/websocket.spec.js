import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-websocket').click()
})

async function compare(page, fixture) {
  await page.getByTestId('websocket-fixture').selectOption(fixture)
  await page.getByTestId('websocket-run').click()
  await expect(page.getByTestId('websocket-fixed-result').getByTestId('websocket-handshake')).toBeVisible()
  await expect(page.getByTestId('websocket-run')).toBeEnabled()
}

function observe(page) {
  const sockets = []
  page.on('websocket', socket => {
    const entry = { url: socket.url(), sent: [], received: [], closed: false }
    sockets.push(entry)
    socket.on('framesent', ({ payload }) => entry.sent.push(JSON.parse(String(payload))))
    socket.on('framereceived', ({ payload }) => entry.received.push(JSON.parse(String(payload))))
    socket.on('close', () => { entry.closed = true })
  })
  return sockets
}

test('allowed origin has two real upgraded sockets and actual JSON frames', async ({ page }) => {
  const sockets = observe(page)
  await compare(page, 'allowed')
  for (const mode of ['vulnerable', 'fixed']) {
    const result = page.getByTestId(`websocket-${mode}-result`)
    await expect(result.getByTestId('websocket-opened')).toHaveText('Yes')
    await expect(result.getByTestId('websocket-handshake')).toHaveText('accepted')
    await expect(result.getByTestId('websocket-messages')).toHaveText('1')
    await expect(result.getByTestId('websocket-deliveries')).toHaveText('1')
    await expect(result.getByTestId('websocket-marker')).toHaveText('HARMLESS_ALPHA_EVENT')
    await expect(result.getByTestId('websocket-close')).toHaveText('1000')
  }
  expect(sockets).toHaveLength(2)
  for (const socket of sockets) {
    expect(socket.url).toMatch(/^ws:\/\/127\.0\.0\.1:8766\/ws\/security\/(vulnerable|fixed)\//)
    expect(socket.sent).toEqual([{ action: 'subscribe', tenant: 'alpha' }])
    expect(socket.received).toEqual([{ kind: 'event', marker: 'HARMLESS_ALPHA_EVENT' }])
    expect(socket.closed).toBe(true)
  }
})

test('real companion-origin handshake is refused before fixed messages', async ({ page }) => {
  const sockets = observe(page)
  await compare(page, 'wrong-origin')
  const vulnerable = page.getByTestId('websocket-vulnerable-result'), fixed = page.getByTestId('websocket-fixed-result')
  await expect(vulnerable.getByTestId('websocket-opened')).toHaveText('Yes')
  await expect(vulnerable.getByTestId('websocket-marker')).toHaveText('HARMLESS_ALPHA_EVENT')
  await expect(fixed.getByTestId('websocket-opened')).toHaveText('No')
  await expect(fixed.getByTestId('websocket-handshake')).toHaveText('origin refused')
  await expect(fixed.getByTestId('websocket-messages')).toHaveText('0')
  await expect(fixed.getByTestId('websocket-marker')).toHaveText('None')
  expect(new URL(await page.getByTestId('websocket-frame').getAttribute('src')).origin).toBe('http://127.0.0.1:8767')
  expect(sockets.find(socket => socket.url.includes('/fixed/')).sent).toEqual([])
})

for (const [fixture, marker, decision] of [['foreign-tenant', 'WS_TENANT_DENIED', 'tenant refused'], ['forbidden-action', 'WS_ACTION_DENIED', 'action refused']]) {
  test(`${fixture} upgrades then refuses the unauthorized message`, async ({ page }) => {
    const sockets = observe(page)
    await compare(page, fixture)
    const fixed = page.getByTestId('websocket-fixed-result')
    await expect(fixed.getByTestId('websocket-opened')).toHaveText('Yes')
    await expect(fixed.getByTestId('websocket-marker')).toHaveText(marker)
    await expect(fixed.getByTestId('websocket-decision')).toHaveText(decision)
    await expect(fixed.getByTestId('websocket-deliveries')).toHaveText('0')
    expect(sockets.find(socket => socket.url.includes('/fixed/')).received).toEqual([{ kind: 'denied', marker }])
  })
}

test('permission revocation happens while the same sockets remain subscribed', async ({ page }) => {
  const sockets = observe(page)
  let liveAtRevocation = false
  page.on('request', request => {
    if (request.url().endsWith('/api/websocket/revoke/')) liveAtRevocation = sockets.length === 2 && sockets.every(socket => !socket.closed && socket.received.length === 1)
  })
  await compare(page, 'permission-revoked')
  expect(liveAtRevocation).toBe(true)
  expect(sockets).toHaveLength(2)
  await expect(page.getByTestId('websocket-revoked')).toBeVisible()
  await expect(page.getByTestId('websocket-vulnerable-result').getByTestId('websocket-deliveries')).toHaveText('2')
  await expect(page.getByTestId('websocket-fixed-result').getByTestId('websocket-deliveries')).toHaveText('1')
  for (const mode of ['vulnerable', 'fixed']) {
    const socket = sockets.find(value => value.url.includes(`/${mode}/`))
    expect(socket.sent).toEqual([{ action: 'subscribe', tenant: 'alpha' }, { action: 'deliver', tenant: 'alpha' }])
    expect(socket.received[0]).toEqual({ kind: 'event', marker: 'HARMLESS_ALPHA_EVENT' })
    expect(socket.received[1].marker).toBe(mode === 'fixed' ? 'WS_PERMISSION_DENIED' : 'HARMLESS_ALPHA_EVENT')
  }
})

test('repeated runs use fresh capabilities and restore the allowed control', async ({ page }) => {
  await compare(page, 'foreign-tenant')
  const first = await page.getByTestId('websocket-frame').getAttribute('src')
  await compare(page, 'allowed')
  const second = await page.getByTestId('websocket-frame').getAttribute('src')
  expect(new URL(first).searchParams.get('run')).not.toBe(new URL(second).searchParams.get('run'))
  expect(new URL(first).searchParams.get('f')).not.toBe(new URL(second).searchParams.get('f'))
  await expect(page.getByTestId('websocket-fixed-result').getByTestId('websocket-marker')).toHaveText('HARMLESS_ALPHA_EVENT')
})

test('leaving a pending preparation does not mount a stale socket harness', async ({ page }) => {
  let release, markEntered
  const entered = new Promise(resolve => { markEntered = resolve })
  const gate = new Promise(resolve => { release = resolve })
  await page.route('**/api/websocket/prepare/', async route => {
    const response = await route.fetch(); markEntered(); await gate
    try { await route.fulfill({ response }) } catch { /* Request was aborted by unmount. */ }
  })
  await page.getByTestId('websocket-run').click()
  await entered
  await page.getByTestId('nav-xss').click()
  release()
  await expect(page.getByTestId('websocket-frame')).toHaveCount(0)
  await page.getByTestId('nav-websocket').click()
  await expect(page.getByTestId('websocket-frame')).toHaveCount(0)
  await expect(page.getByTestId('websocket-run')).toBeEnabled()
})
