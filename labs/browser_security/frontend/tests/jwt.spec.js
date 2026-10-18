import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-jwt').click()
})

async function compare(page, fixture) {
  await page.getByTestId('jwt-fixture').selectOption(fixture)
  await page.getByTestId('jwt-run').click()
  const vulnerable = page.getByTestId('jwt-vulnerable-result')
  const fixed = page.getByTestId('jwt-fixed-result')
  await expect(vulnerable.getByTestId('jwt-marker')).toBeVisible()
  await expect(fixed.getByTestId('jwt-marker')).toBeVisible()
  await expect(page.getByTestId('jwt-run')).toBeEnabled()
  return { vulnerable, fixed }
}

test('JWT: valid tokens authorize while a valid forbidden subject still fails authorization', async ({ page }) => {
  let results = await compare(page, 'normal')
  for (const result of Object.values(results)) {
    await expect(result.getByTestId('jwt-marker')).toHaveText('JWT_PROTECTED_REPORT_MARKER')
    await expect(result.getByTestId('jwt-outcome')).toHaveText('accepted')
  }
  await expect(results.fixed.getByTestId('jwt-validation')).toHaveText('verified')
  await expect(results.vulnerable.getByTestId('jwt-validation')).toHaveText('skipped')
  await page.getByTestId('jwt-fixture').selectOption('wrong-subject')
  await expect(results.fixed.getByTestId('jwt-marker')).toHaveCount(0)
  await expect(page.getByTestId('jwt-token')).toHaveCount(0)
  results = await compare(page, 'wrong-subject')
  for (const result of Object.values(results)) {
    await expect(result.getByTestId('jwt-marker')).toHaveText('No report returned')
    await expect(result.getByTestId('jwt-reason')).toContainText('not authorized')
  }
  await expect(results.fixed.getByTestId('jwt-validation')).toHaveText('verified')
})

test('JWT: edited and unsigned tokens cannot pass signature and algorithm checks', async ({ page }) => {
  for (const [fixture, reason] of [['tampered', 'Signature verification failed'], ['unsigned', 'allowlist']]) {
    const results = await compare(page, fixture)
    await expect(results.vulnerable.getByTestId('jwt-marker')).toHaveText('JWT_PROTECTED_REPORT_MARKER')
    await expect(results.fixed.getByTestId('jwt-marker')).toHaveText('No report returned')
    await expect(results.fixed.getByTestId('jwt-reason')).toContainText(reason)
  }
  await expect(page.getByTestId('jwt-header')).toContainText('"alg": "none"')
  await expect(page.getByTestId('jwt-claims')).toContainText('"sub": "report-reader"')
  await expect(page.getByTestId('jwt-token')).toHaveText(/^[\w-]+\.[\w-]+\.$/)
})

test('JWT: expiration, not-before, required claims, issuer and audience are independently enforced', async ({ page }) => {
  for (const [fixture, reason] of [['expired', 'expired'], ['future', 'not valid yet'], ['missing-exp', 'missing: exp'], ['wrong-issuer', 'issuer'], ['wrong-audience', 'audience']]) {
    const results = await compare(page, fixture)
    await expect(results.vulnerable.getByTestId('jwt-outcome')).toHaveText('accepted')
    await expect(results.fixed.getByTestId('jwt-outcome')).toHaveText('rejected')
    await expect(results.fixed.getByTestId('jwt-marker')).toHaveText('No report returned')
    await expect(results.fixed.getByTestId('jwt-reason')).toContainText(reason)
  }
})
