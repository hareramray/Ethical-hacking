import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-auth').click()
})

async function compare(page, scenario) {
  await page.getByTestId('auth-scenario').selectOption(scenario)
  await page.getByTestId('auth-run').click()
  await expect(page.getByTestId('auth-run')).toBeEnabled({ timeout: 20000 })
  const vulnerable = page.getByTestId('auth-vulnerable-result')
  const fixed = page.getByTestId('auth-fixed-result')
  await expect(vulnerable.locator('.traversal-outcome')).toBeVisible()
  await expect(fixed.locator('.traversal-outcome')).toBeVisible()
  return { vulnerable, fixed }
}

test('Auth: successful login rotates the fixed token and denies its saved predecessor', async ({ page }) => {
  const { vulnerable, fixed } = await compare(page, 'rotation')
  await expect(vulnerable.locator('.traversal-outcome')).toHaveText('exposed')
  await expect(fixed.locator('.traversal-outcome')).toHaveText('protected')
  await expect(vulnerable.locator('.auth-steps')).toContainText('Token unchanged: S1 -> S1')
  await expect(fixed.locator('.auth-steps')).toContainText('Token changed: S1 -> S2')
  await expect(fixed.locator('.auth-checks [data-passed="false"]')).toHaveCount(0)
  await expect(vulnerable.locator('.auth-checks [data-passed="false"]')).toHaveCount(2)
})

test('Auth: logout replay is rejected server-side only by the fixed flow', async ({ page }) => {
  const { vulnerable, fixed } = await compare(page, 'logout')
  await expect(vulnerable.locator('.auth-steps pre').last()).toContainText('ALICE_AUTH_SESSION_FIXTURE')
  await expect(fixed.locator('.auth-steps pre').last()).toContainText('Access denied; no marker')
  await expect(fixed.locator('.auth-checks [data-passed="false"]')).toHaveCount(0)
  await expect(vulnerable.locator('.auth-checks [data-passed="false"]')).toHaveCount(1)
})

test('Auth: expiration and reuse are enforced while a first valid reset still succeeds', async ({ page }) => {
  let results = await compare(page, 'reset-expiry')
  await expect(results.fixed.locator('.auth-steps')).toContainText('expired')
  await expect(results.fixed.locator('.auth-steps')).toContainText('(t=160)')
  await expect(results.vulnerable.locator('.traversal-outcome')).toHaveText('exposed')
  results = await compare(page, 'reset-reuse')
  await expect(results.fixed.locator('.auth-steps')).toContainText('already_used')
  await expect(results.fixed.locator('.auth-checks [data-passed="false"]')).toHaveCount(0)
  await expect(results.vulnerable.locator('.traversal-outcome')).toHaveText('exposed')
})

test('Auth: valid-reset and invalid-password controls pass and switching clears previous results', async ({ page }) => {
  let results = await compare(page, 'legitimate-reset')
  for (const result of Object.values(results)) {
    await expect(result.locator('.traversal-outcome')).toHaveText('control_passed')
    await expect(result.locator('.auth-steps')).toContainText('ALICE_AUTH_SESSION_FIXTURE')
  }
  await page.getByTestId('auth-scenario').selectOption('invalid-password')
  await expect(results.fixed.locator('.auth-steps')).toHaveCount(0)
  results = await compare(page, 'invalid-password')
  for (const result of Object.values(results)) {
    await expect(result.locator('.traversal-outcome')).toHaveText('control_passed')
    await expect(result).not.toContainText('ALICE_AUTH_SESSION_FIXTURE')
    await expect(result.locator('.auth-checks [data-passed="false"]')).toHaveCount(0)
  }
})
