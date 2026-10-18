import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-sql').click()
})

async function compare(page, fixture) {
  if (fixture) await page.getByTestId('sql-fixture').selectOption(fixture)
  await page.getByTestId('sql-run').click()
  await expect(page.getByTestId('sql-run')).toBeEnabled()
  const vulnerable = page.getByTestId('sql-vulnerable-result')
  const fixed = page.getByTestId('sql-fixed-result')
  await expect(vulnerable.locator('.traversal-outcome')).toBeVisible()
  await expect(fixed.locator('.traversal-outcome')).toBeVisible()
  return { vulnerable, fixed }
}

test('SQL: ordinary public search works with both handlers', async ({ page }) => {
  const results = await compare(page, 'normal')
  for (const result of Object.values(results)) {
    await expect(result.locator('.sql-rows')).toContainText('PUBLIC_NOTEBOOK')
    await expect(result.locator('.traversal-outcome')).toHaveText('read')
  }
  await expect(results.fixed.locator('.sql-query')).toContainText('name = ?')
  await expect(results.fixed.locator('.sql-parameters')).toHaveText('["Notebook"]')
})

test('SQL: injected condition exposes only the vulnerable fixture', async ({ page }) => {
  const { vulnerable, fixed } = await compare(page, 'tautology')
  await expect(vulnerable.locator('.sql-rows')).toContainText('PRIVATE_SQL_SENTINEL_ONLY_FOR_LAB')
  await expect(fixed.locator('.sql-rows')).toHaveText('No rows returned.')
  await expect(fixed).not.toContainText('PRIVATE_SQL_SENTINEL_ONLY_FOR_LAB')
  await expect(fixed.locator('.sql-parameters')).toContainText("' OR 1=1 -- ")
  await compare(page, 'missing')
  await expect(vulnerable.locator('.sql-rows')).toHaveText('No rows returned.')
})

test('SQL: legitimate apostrophes succeed with parameters and show concatenation errors', async ({ page }) => {
  const { vulnerable, fixed } = await compare(page, 'quoted')
  await expect(vulnerable.locator('.traversal-outcome')).toHaveText('query_error')
  await expect(vulnerable.locator('.sql-rows')).toHaveText('No rows returned.')
  await expect(fixed.locator('.sql-rows')).toContainText('PUBLIC_QUOTED_NAME')
  await expect(fixed.locator('.sql-parameters')).toHaveText('["Reader\'s guide"]')
})

test('SQL: custom text stays inert and invalid input clears prior evidence', async ({ page }) => {
  await page.getByTestId('sql-input').fill('<img id=SQL_TEXT_ONLY src=x>')
  let results = await compare(page)
  for (const result of Object.values(results)) {
    await expect(result).toContainText('<img id=SQL_TEXT_ONLY src=x>')
    await expect(result.locator('img')).toHaveCount(0)
    await expect(result.locator('.sql-rows')).toHaveText('No rows returned.')
  }
  await expect(page.locator('#SQL_TEXT_ONLY')).toHaveCount(0)
  await compare(page, 'tautology')
  await page.getByTestId('sql-input').fill('x'.repeat(257))
  results = await compare(page)
  for (const result of Object.values(results)) {
    await expect(result.locator('.traversal-outcome')).toHaveText('invalid')
    await expect(result).not.toContainText('PRIVATE_SQL_SENTINEL_ONLY_FOR_LAB')
    await expect(result).toContainText('400')
  }
})
