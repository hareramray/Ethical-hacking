import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-archive').click()
})

async function compare(page, fixture) {
  await page.getByTestId('archive-fixture').selectOption(fixture)
  await page.getByTestId('archive-run').click()
  const vulnerable = page.getByTestId('archive-vulnerable-result')
  const fixed = page.getByTestId('archive-fixed-result')
  await expect(vulnerable.getByTestId('archive-after')).toBeVisible()
  await expect(fixed.getByTestId('archive-after')).toBeVisible()
  await expect(page.getByTestId('archive-run')).toBeEnabled()
  return { vulnerable, fixed }
}

test('ZIP: a legitimate nested file is preserved by both handlers', async ({ page }) => {
  const results = await compare(page, 'normal')
  await expect(page.getByTestId('archive-entries')).toContainText('docs/hello.txt [regular file]')
  for (const result of Object.values(results)) {
    await expect(result.locator('.traversal-outcome')).toHaveText('extracted')
    await expect(result.getByTestId('archive-after')).toHaveText('extract/docs/hello.txt (17 bytes)\nZIP_NORMAL_MARKER')
    await expect(result.getByTestId('archive-outside')).toHaveText('No')
    await expect(result.getByTestId('archive-before')).toHaveText('0')
  }
})

test('ZIP: parent and backslash names write only into the bounded sibling fixture', async ({ page }) => {
  for (const fixture of ['traversal', 'backslash', 'mixed']) {
    const results = await compare(page, fixture)
    await expect(results.vulnerable.getByTestId('archive-outside')).toHaveText('Yes, inside the disposable workspace')
    await expect(results.vulnerable.getByTestId('archive-after')).toContainText('outside.txt (18 bytes)\nZIP_SIBLING_MARKER')
    await expect(results.fixed.locator('.traversal-outcome')).toHaveText('blocked')
    await expect(results.fixed.getByTestId('archive-write-count')).toHaveText('0')
    await expect(results.fixed.getByTestId('archive-after')).toHaveText('No files written.')
  }
  await page.getByTestId('archive-fixture').selectOption('normal')
  await expect(page.getByTestId('archive-entries')).toHaveCount(0)
  await expect(page.getByTestId('archive-vulnerable-result').getByTestId('archive-after')).toHaveCount(0)
})

test('ZIP: tiny count and expanded-byte overflow fixtures stop before fixed writes', async ({ page }) => {
  for (const [fixture, reason] of [['count', 'Entry-count'], ['expanded', 'Total expanded'], ['entry', 'Per-entry expanded'], ['compressed', 'Per-entry compressed']]) {
    const results = await compare(page, fixture)
    await expect(results.vulnerable.locator('.traversal-outcome')).toHaveText('extracted')
    await expect(results.fixed.locator('.traversal-outcome')).toHaveText('blocked')
    await expect(results.fixed.getByTestId('archive-reason')).toContainText(reason)
    await expect(results.fixed.getByTestId('archive-write-count')).toHaveText('0')
  }
})

test('ZIP: duplicate names, collisions, links, and absolute paths have explicit outcomes', async ({ page }) => {
  let results = await compare(page, 'duplicate')
  await expect(results.vulnerable.getByTestId('archive-write-count')).toHaveText('2')
  await expect(results.vulnerable.getByTestId('archive-after-count')).toHaveText('1')
  await expect(results.vulnerable.getByTestId('archive-after')).toContainText('SECOND_MARKER')
  await expect(results.fixed.getByTestId('archive-write-count')).toHaveText('0')
  results = await compare(page, 'collision')
  await expect(results.vulnerable.locator('.traversal-outcome')).toHaveText('error')
  await expect(results.vulnerable.getByTestId('archive-after')).toContainText('FILE_MARKER')
  await expect(results.fixed.getByTestId('archive-write-count')).toHaveText('0')
  results = await compare(page, 'symlink')
  await expect(page.getByTestId('archive-entries')).toContainText('[symlink]')
  await expect(results.vulnerable.getByTestId('archive-after')).toContainText('../outside.txt')
  await expect(results.fixed.getByTestId('archive-reason')).toContainText('links and special entries')
  for (const fixture of ['absolute', 'drive']) {
    results = await compare(page, fixture)
    for (const result of Object.values(results)) {
      await expect(result.locator('.traversal-outcome')).toHaveText('blocked')
      await expect(result.getByTestId('archive-write-count')).toHaveText('0')
    }
  }
})
