import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-access').click()
  await expect(page.getByTestId('access-run')).toBeEnabled()
})

async function persona(page, actor) {
  await page.getByTestId('access-actor').selectOption(actor)
  await expect(page.getByTestId('access-run')).toBeEnabled()
  await expect(page.getByTestId('access-actor')).toHaveValue(actor)
}

async function compare(page, record, action = 'read') {
  await page.getByTestId('access-record').selectOption(record)
  await page.getByTestId('access-action').selectOption(action)
  await page.getByTestId('access-run').click()
  await expect(page.getByTestId('access-run')).toBeEnabled()
  const vulnerable = page.getByTestId('access-vulnerable-result')
  const fixed = page.getByTestId('access-fixed-result')
  await expect(vulnerable.locator('.traversal-outcome')).toBeVisible()
  await expect(fixed.locator('.traversal-outcome')).toBeVisible()
  return { vulnerable, fixed }
}

test('access: peer IDOR is denied by fixed handler while owner reads still work', async ({ page }) => {
  await persona(page, 'alice')
  let results = await compare(page, 'bob-a')
  await expect(results.vulnerable.locator('.traversal-content')).toHaveText('BOB_PRIVATE_LAB_RECORD')
  await expect(results.fixed.locator('.traversal-outcome')).toHaveText('denied')
  await expect(results.fixed).toContainText('403')
  await expect(results.fixed).not.toContainText('BOB_PRIVATE_LAB_RECORD')
  results = await compare(page, 'alice-a')
  for (const result of Object.values(results)) {
    await expect(result.locator('.traversal-outcome')).toHaveText('allowed')
    await expect(result.locator('.traversal-content')).toHaveText('ALICE_PRIVATE_LAB_RECORD')
    await expect(result).toContainText('200')
  }
})

test('access: admin review stays within the admin tenant', async ({ page }) => {
  await persona(page, 'admin-a')
  let results = await compare(page, 'bob-a', 'review')
  await expect(results.fixed.locator('.traversal-content')).toHaveText('BOB_PRIVATE_LAB_RECORD')
  results = await compare(page, 'carol-b', 'review')
  await expect(results.vulnerable.locator('.traversal-content')).toHaveText('CAROL_PRIVATE_LAB_RECORD')
  await expect(results.fixed.locator('.traversal-outcome')).toHaveText('denied')
  await expect(results.fixed).toContainText('403')
  await expect(results.fixed).not.toContainText('CAROL_PRIVATE_LAB_RECORD')
})

test('access: anonymous is rejected by both modes and stale protected content clears', async ({ page }) => {
  await persona(page, 'alice')
  await compare(page, 'alice-a')
  await persona(page, 'anonymous')
  const results = await compare(page, 'alice-a')
  for (const result of Object.values(results)) {
    await expect(result.locator('.traversal-outcome')).toHaveText('unauthenticated')
    await expect(result).toContainText('401')
    await expect(result.locator('.traversal-content')).toHaveCount(0)
    await expect(result).not.toContainText('ALICE_PRIVATE_LAB_RECORD')
  }
  await page.reload()
  await page.getByTestId('nav-access').click()
  await expect(page.getByTestId('access-run')).toBeEnabled()
  await expect(page.getByTestId('access-actor')).toHaveValue('anonymous')
})
