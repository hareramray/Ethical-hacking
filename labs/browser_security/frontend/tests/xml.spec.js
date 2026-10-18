import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-xml').click()
})

async function compare(page, fixture) {
  await page.getByTestId('xml-fixture').selectOption(fixture)
  await page.getByTestId('xml-run').click()
  await expect(page.getByTestId('xml-run')).toBeEnabled()
  const vulnerable = page.getByTestId('xml-vulnerable-result')
  const fixed = page.getByTestId('xml-fixed-result')
  await expect(vulnerable.locator('.traversal-outcome')).toBeVisible()
  await expect(fixed.locator('.traversal-outcome')).toBeVisible()
  return { vulnerable, fixed }
}

test('XML: ordinary text and built-in entities work in both parsers and render as text', async ({ page }) => {
  let results = await compare(page, 'normal')
  for (const result of Object.values(results)) {
    await expect(result.locator('.traversal-outcome')).toHaveText('parsed')
    await expect(result.getByTestId('xml-text')).toHaveText('Hello from the XML fixture.')
    await expect(result.getByTestId('xml-resolution-count')).toHaveText('0')
  }
  results = await compare(page, 'builtin')
  for (const result of Object.values(results)) {
    await expect(result.locator('.traversal-outcome')).toHaveText('parsed')
    await expect(result.getByTestId('xml-text')).toHaveText('Tea & biscuits <served>')
    await expect(result.locator('served')).toHaveCount(0)
  }
  await expect(page.getByTestId('xml-source')).toContainText('&amp;')
})

test('XML: external entity resolves only in the vulnerable parser and fixed mode blocks before resolution', async ({ page }) => {
  const { vulnerable, fixed } = await compare(page, 'external')
  await expect(vulnerable.locator('.traversal-outcome')).toHaveText('parsed')
  await expect(vulnerable.getByTestId('xml-text')).toHaveText('PRIVATE_XML_SENTINEL_ONLY_FOR_LAB')
  await expect(vulnerable.getByTestId('xml-resolution-count')).toHaveText('1')
  await expect(vulnerable).toContainText('in_memory_marker')
  await expect(fixed.locator('.traversal-outcome')).toHaveText('blocked')
  await expect(fixed.getByTestId('xml-resolution-count')).toHaveText('0')
  await expect(fixed.getByTestId('xml-text')).toHaveText('No application text returned.')
  await expect(fixed).not.toContainText('PRIVATE_XML_SENTINEL_ONLY_FOR_LAB')
})

test('XML: unknown resources and malformed documents clear earlier output and explain distinct failures', async ({ page }) => {
  await compare(page, 'external')
  let results = await compare(page, 'unknown')
  for (const result of Object.values(results)) {
    await expect(result.locator('.traversal-outcome')).toHaveText('blocked')
    await expect(result.getByTestId('xml-text')).toHaveText('No application text returned.')
    await expect(result).not.toContainText('PRIVATE_XML_SENTINEL_ONLY_FOR_LAB')
  }
  await expect(results.vulnerable.getByTestId('xml-resolution-count')).toHaveText('1')
  await expect(results.fixed.getByTestId('xml-resolution-count')).toHaveText('0')
  results = await compare(page, 'malformed')
  for (const result of Object.values(results)) {
    await expect(result.locator('.traversal-outcome')).toHaveText('parse_error')
    await expect(result.getByTestId('xml-resolution-count')).toHaveText('0')
    await expect(result.getByTestId('xml-text')).toHaveText('No application text returned.')
    await expect(result).toContainText('XML parser error at line 1')
  }
})
