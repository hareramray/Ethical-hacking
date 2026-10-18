import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-ssrf').click()
})

async function compare(page, fixture) {
  if (fixture) await page.getByTestId('ssrf-fixture').selectOption(fixture)
  await page.getByTestId('ssrf-run').click()
  await expect(page.getByTestId('ssrf-run')).toBeEnabled()
  const vulnerable = page.getByTestId('ssrf-vulnerable-result')
  const fixed = page.getByTestId('ssrf-fixed-result')
  await expect(vulnerable.locator('.traversal-outcome')).toBeVisible()
  await expect(fixed.locator('.traversal-outcome')).toBeVisible()
  return { vulnerable, fixed }
}

test('SSRF: public information and allowed redirect work with both fetchers', async ({ page }) => {
  for (const fixture of ['public', 'redirect-public']) {
    for (const result of Object.values(await compare(page, fixture))) {
      await expect(result.locator('.traversal-outcome')).toHaveText('read')
      await expect(result.locator('.ssrf-marker')).toHaveText('PUBLIC_SSRF_FIXTURE')
      await expect(result.locator('.ssrf-trace pre')).toHaveCount(fixture === 'public' ? 1 : 2)
    }
  }
})

test('SSRF: private fixture and redirect are blocked before the fixed private request', async ({ page }) => {
  for (const fixture of ['private', 'redirect-private']) {
    const { vulnerable, fixed } = await compare(page, fixture)
    await expect(vulnerable.locator('.ssrf-marker')).toHaveText('PRIVATE_SSRF_SENTINEL_ONLY_FOR_LAB')
    await expect(fixed.locator('.traversal-outcome')).toHaveText('blocked')
    await expect(fixed.locator('.ssrf-marker')).toHaveText('No marker returned.')
    await expect(fixed.locator('.ssrf-trace pre')).toHaveCount(fixture === 'private' ? 0 : 1)
    if (fixture === 'redirect-private') await expect(fixed.locator('.ssrf-trace')).toContainText('Location: http://private.fixture.test/marker')
  }
})

test('SSRF: outside destinations and redirect loops stop at their limits', async ({ page }) => {
  for (const fixture of ['external', 'redirect-external', 'loop']) {
    const results = await compare(page, fixture)
    for (const result of Object.values(results)) {
      await expect(result.locator('.traversal-outcome')).toHaveText(fixture === 'loop' ? 'request_limit' : 'boundary_blocked')
      await expect(result.locator('.ssrf-marker')).toHaveText('No marker returned.')
      await expect(result.locator('.ssrf-trace pre')).toHaveCount(fixture === 'loop' ? 4 : fixture === 'external' ? 0 : 1)
    }
  }
})

test('SSRF: invalid custom URLs clear prior markers and remain inert text', async ({ page }) => {
  await compare(page, 'private')
  await page.getByTestId('ssrf-target').fill('<img id="SSRF_TEXT_ONLY" src=x>')
  for (const result of Object.values(await compare(page))) {
    await expect(result.locator('.traversal-outcome')).toHaveText('invalid')
    await expect(result.locator('.ssrf-marker')).toHaveText('No marker returned.')
    await expect(result.locator('.ssrf-trace pre')).toHaveCount(0)
    await expect(result).toContainText('400')
  }
  await expect(page.locator('#SSRF_TEXT_ONLY')).toHaveCount(0)
  await expect(page.locator('.traversal-compared-path')).toContainText('<img id="SSRF_TEXT_ONLY" src=x>')
})
