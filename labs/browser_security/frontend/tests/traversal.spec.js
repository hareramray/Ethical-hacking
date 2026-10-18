import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-traversal').click()
})

async function compare(page, preset) {
  if (preset) await page.getByTestId('traversal-fixture').selectOption(preset)
  await page.getByTestId('traversal-run').click()
  await expect(page.getByTestId('traversal-run')).toBeEnabled()
  const vulnerable = page.getByTestId('traversal-vulnerable-result')
  const fixed = page.getByTestId('traversal-fixed-result')
  await expect(vulnerable.locator('.traversal-outcome')).toBeVisible()
  await expect(fixed.locator('.traversal-outcome')).toBeVisible()
  return { vulnerable, fixed }
}

test('path traversal: public downloads still work in both handlers', async ({ page }) => {
  await expect(page.getByTestId('traversal-tree')).toContainText('private/sentinel.txt')
  for (const [preset, marker] of [['readme', 'PUBLIC_README_OK'], ['nested', 'NESTED_NOTES_OK']]) {
    const { vulnerable, fixed } = await compare(page, preset)
    for (const result of [vulnerable, fixed]) {
      await expect(result.locator('.traversal-outcome')).toHaveText('read')
      await expect(result.locator('.traversal-content')).toHaveText(marker)
      await expect(result).toContainText('200')
    }
  }
})

test('path traversal: parent, backslash and prefix sibling compare vulnerable and fixed behavior', async ({ page }) => {
  for (const [preset, marker] of [['parent', 'PRIVATE_SENTINEL_ONLY_FOR_LAB'], ['backslash', 'PRIVATE_SENTINEL_ONLY_FOR_LAB'], ['prefix', 'SIBLING_PREFIX_SENTINEL']]) {
    const { vulnerable, fixed } = await compare(page, preset)
    await expect(vulnerable.locator('.traversal-content')).toHaveText(marker)
    await expect(fixed.locator('.traversal-outcome')).toHaveText('blocked')
    await expect(fixed).toContainText('403')
    await expect(fixed.locator('.traversal-content')).toHaveCount(0)
    await expect(fixed).not.toContainText(marker)
  }
})

test('path traversal: missing and outer-boundary paths clear previously read content', async ({ page }) => {
  await compare(page, 'parent')
  const missing = await compare(page, 'missing')
  for (const result of Object.values(missing)) {
    await expect(result.locator('.traversal-outcome')).toHaveText('not_found')
    await expect(result).toContainText('404')
    await expect(result).not.toContainText('PRIVATE_SENTINEL_ONLY_FOR_LAB')
  }
  await page.getByTestId('traversal-path').fill('../../outside-sentinel.txt')
  const outside = await compare(page)
  for (const result of Object.values(outside)) {
    await expect(result.locator('.traversal-outcome')).toHaveText('blocked')
    await expect(result).toContainText('outer disposable lab boundary')
    await expect(result.locator('.traversal-content')).toHaveCount(0)
  }
})

test('path traversal: custom path text is encoded once and rendered literally', async ({ page }) => {
  await page.getByTestId('traversal-path').fill('%2e%2e%2fprivate%2fsentinel.txt')
  let results = await compare(page)
  for (const result of Object.values(results)) {
    await expect(result.locator('.traversal-outcome')).toHaveText('not_found')
    await expect(result).toContainText('%2e%2e%2fprivate%2fsentinel.txt')
  }
  await page.getByTestId('traversal-path').fill('<img id=TRAVERSAL_RENDER_TEST src=x>')
  results = await compare(page)
  for (const result of Object.values(results)) {
    await expect(result).toContainText('<img id=TRAVERSAL_RENDER_TEST src=x>')
    await expect(result.locator('img')).toHaveCount(0)
  }
  await expect(page.locator('#TRAVERSAL_RENDER_TEST')).toHaveCount(0)
})
