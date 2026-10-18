import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-template').click()
})

async function compare(page, fixture) {
  await page.getByTestId('template-fixture').selectOption(fixture)
  await page.getByTestId('template-run').click()
  const vulnerable = page.getByTestId('template-vulnerable-result')
  const fixed = page.getByTestId('template-fixed-result')
  await expect(vulnerable.getByTestId('template-rendered')).toBeVisible()
  await expect(fixed.getByTestId('template-rendered')).toBeVisible()
  await expect(page.getByTestId('template-run')).toBeEnabled()
  return { vulnerable, fixed }
}

test('SSTI: ordinary names still render in both implementations', async ({ page }) => {
  const results = await compare(page, 'normal')
  for (const result of Object.values(results)) {
    await expect(result.getByTestId('template-rendered')).toHaveText('Hello, Ada.')
    await expect(result.getByTestId('template-marker-exposed')).toHaveText('No')
  }
  await expect(results.fixed.getByTestId('template-source')).toHaveText('Hello, {{ name }}.')
  await expect(results.fixed.getByTestId('template-context')).toContainText('"name": "Ada"')
})

test('SSTI: context resolution and conditional evaluation require compiled source', async ({ page }) => {
  let results = await compare(page, 'marker')
  await expect(results.vulnerable.getByTestId('template-rendered')).toHaveText('Hello, TEMPLATE_CONTEXT_SENTINEL.')
  await expect(results.vulnerable.getByTestId('template-marker-exposed')).toHaveText('Yes')
  await expect(results.fixed.getByTestId('template-rendered')).toHaveText('Hello, {{ marker }}.')
  await expect(results.fixed.getByTestId('template-marker-exposed')).toHaveText('No')
  await page.getByTestId('template-fixture').selectOption('conditional')
  await expect(results.vulnerable.getByTestId('template-rendered')).toHaveCount(0)
  results = await compare(page, 'conditional')
  await expect(results.vulnerable.getByTestId('template-rendered')).toHaveText('Hello, template_context_sentinel.')
  await expect(results.fixed.getByTestId('template-rendered')).toHaveText('Hello, {% if enabled %}{{ marker|lower }}{% endif %}.')
})

test('SSTI: HTML autoescaping is visible and output remains inert in the dashboard', async ({ page }) => {
  const results = await compare(page, 'html')
  await expect(results.vulnerable.getByTestId('template-rendered')).toHaveText('Hello, <strong id="TEMPLATE_TEXT_ONLY">Ada & Bea</strong>.')
  await expect(results.fixed.getByTestId('template-rendered')).toHaveText('Hello, &lt;strong id=&quot;TEMPLATE_TEXT_ONLY&quot;&gt;Ada &amp; Bea&lt;/strong&gt;.')
  await expect(results.fixed.locator('.traversal-outcome')).toHaveText('escaped')
  await expect(page.locator('#TEMPLATE_TEXT_ONLY')).toHaveCount(0)
  for (const result of Object.values(results)) await expect(result.getByTestId('template-rendered').locator('strong')).toHaveCount(0)
})
