import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-framing').click()
  await expect(page.getByTestId('framing-run')).toBeEnabled()
})

async function compare(page, fixture) {
  await page.getByTestId('framing-fixture').selectOption(fixture)
  const responsePromise = page.waitForResponse(response => {
    const url = new URL(response.url())
    return url.pathname === '/lab/framing/target/' && url.searchParams.get('mode') === 'fixed'
      && url.searchParams.get('fixture') === fixture
  })
  await page.getByTestId('framing-run').click()
  const fixedResponse = await responsePromise
  const vulnerable = page.getByTestId('framing-vulnerable-result')
  const fixed = page.getByTestId('framing-fixed-result')
  await expect(vulnerable.locator('.traversal-outcome')).toBeVisible()
  await expect(fixed.locator('.traversal-outcome')).toBeVisible()
  await expect(page.getByTestId('framing-run')).toBeEnabled()
  return { vulnerable, fixed, fixedResponse }
}

async function clickPretendLabel(page, mode) {
  // Bring the top-level iframe into view before inspecting its nested overlay.
  // An offscreen cross-origin frame can throttle animation frames used by
  // Playwright's nested-element stability wait.
  await page.getByTestId(`framing-${mode}-frame`).scrollIntoViewIfNeeded()
  const harness = page.frameLocator(`[data-testid="framing-${mode}-frame"]`)
  const overlay = harness.locator('#pretend')
  await expect(overlay).toBeVisible()
  await expect(overlay).toBeInViewport({ ratio: 1 })
  const box = await overlay.boundingBox()
  expect(box).not.toBeNull()
  await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2)
  const result = page.getByTestId(`framing-${mode}-result`)
  await expect(result.getByTestId('framing-clicks')).toHaveText('1')
  await expect(result.getByTestId('framing-trusted')).toHaveText('Yes')
  await expect(harness.frameLocator('#target').locator('#clicks')).toHaveText('1')
  await harness.locator('#overlay-toggle').uncheck()
  await expect(overlay).toBeHidden()
  await expect(harness.frameLocator('#target').getByRole('button', { name: 'Practice action: increment local counter' })).toBeVisible()
}

for (const fixture of ['csp-self', 'xfo-sameorigin']) {
  test(`framing: ${fixture} produces a real browser refusal while the unrestricted target accepts a click`, async ({ page }) => {
    const messages = []
    page.on('console', message => messages.push(message.text()))
    const { vulnerable, fixed, fixedResponse } = await compare(page, fixture)
    await expect(vulnerable.getByTestId('framing-ready')).toHaveText('Yes')
    await expect(fixed.getByTestId('framing-ready')).toHaveText('No')
    await expect(fixed.locator('.traversal-outcome')).toHaveText('no readiness')
    await expect(fixed).toContainText('Inspect the target response and browser console')
    await expect(fixed.getByTestId('framing-clicks')).toHaveText('0')
    const headers = fixedResponse.headers()
    if (fixture === 'csp-self') {
      expect(headers['content-security-policy']).toContain("frame-ancestors 'self'")
      expect(headers['x-frame-options']).toBeUndefined()
      await expect.poll(() => messages.some(message => /frame-ancestors/.test(message) && /violates|refused|blocked/i.test(message))).toBe(true)
    } else {
      expect(headers['x-frame-options']).toBe('SAMEORIGIN')
      expect(headers['content-security-policy']).not.toContain('frame-ancestors')
      await expect.poll(() => messages.some(message => /X-Frame-Options/i.test(message) && /refused|blocked/i.test(message))).toBe(true)
    }
    await expect(page.frameLocator('[data-testid="framing-fixed-frame"]').frameLocator('#target').locator('#practice')).toHaveCount(0)
    await clickPretendLabel(page, 'vulnerable')
  })
}

test('framing: both exact ancestor origins allow an integration and a real overlay click', async ({ page }) => {
  const { vulnerable, fixed, fixedResponse } = await compare(page, 'allowed-integration')
  const mainOrigin = new URL(page.url()).origin
  const harnessOrigin = new URL(await page.getByTestId('framing-fixed-frame').getAttribute('src')).origin
  expect(harnessOrigin).not.toBe(mainOrigin)
  expect(fixedResponse.headers()['content-security-policy']).toContain(`frame-ancestors ${mainOrigin} ${harnessOrigin}`)
  for (const result of [vulnerable, fixed]) {
    await expect(result.getByTestId('framing-ready')).toHaveText('Yes')
    await expect(result.getByTestId('framing-clicks')).toHaveText('0')
  }
  await clickPretendLabel(page, 'fixed')
  await clickPretendLabel(page, 'vulnerable')
})

test('framing: synthetic clicks do not count and rerunning destroys old counter state', async ({ page }) => {
  await compare(page, 'allowed-integration')
  const oldSource = await page.getByTestId('framing-fixed-frame').getAttribute('src')
  const target = page.frames().find(frame => frame.url().includes('/lab/framing/target/') && new URL(frame.url()).searchParams.get('mode') === 'fixed')
  expect(target).toBeTruthy()
  await target.locator('#practice').evaluate(button => button.click())
  await expect(target.locator('#clicks')).toHaveText('0')
  await expect(page.getByTestId('framing-fixed-result').getByTestId('framing-trusted')).toHaveText('No')
  await clickPretendLabel(page, 'fixed')
  await compare(page, 'allowed-integration')
  expect(await page.getByTestId('framing-fixed-frame').getAttribute('src')).not.toBe(oldSource)
  await expect(page.getByTestId('framing-fixed-result').getByTestId('framing-clicks')).toHaveText('0')
  const peer = new URL(oldSource).origin
  expect((await page.request.get(peer + '/api/bootstrap')).status()).toBe(404)
  expect((await page.request.get(peer + '/lab/framing/target.js')).status()).toBe(404)
  await page.getByTestId('nav-xss').click()
  await expect(page.getByTestId('framing-fixed-frame')).toHaveCount(0)
})
