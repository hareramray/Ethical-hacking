import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-write').click()
})

async function compare(page, fixture) {
  await page.getByTestId('write-fixture').selectOption(fixture)
  await page.getByTestId('write-run').click()
  const vulnerable = page.getByTestId('write-vulnerable-result')
  const fixed = page.getByTestId('write-fixed-result')
  await expect(vulnerable.getByTestId('write-after')).toBeVisible()
  await expect(fixed.getByTestId('write-after')).toBeVisible()
  await expect(page.getByTestId('write-run')).toBeEnabled()
  return { vulnerable, fixed }
}

test('API writes: legitimate display-name edit commits in both fresh stores', async ({ page }) => {
  const results = await compare(page, 'own')
  await expect(page.getByTestId('write-actor')).toContainText('"id": "user-ada"')
  for (const result of Object.values(results)) {
    await expect(result.locator('.traversal-outcome')).toHaveText('updated')
    await expect(result.getByTestId('write-before')).toContainText('"displayName": "Ada"')
    await expect(result.getByTestId('write-after')).toContainText('"displayName": "Ada Lovelace"')
    await expect(result.getByTestId('write-rows-changed')).toHaveText('1')
    await expect(result.getByTestId('write-changed-fields')).toHaveText('displayName')
  }
})

test('API writes: peer and cross-tenant object updates are denied before mutation', async ({ page }) => {
  for (const fixture of ['peer', 'cross-tenant']) {
    const { vulnerable, fixed } = await compare(page, fixture)
    await expect(vulnerable.getByTestId('write-after')).toContainText('"displayName": "Changed by Ada"')
    await expect(fixed.locator('.traversal-outcome')).toHaveText('denied')
    await expect(fixed.getByTestId('write-rows-changed')).toHaveText('0')
    await expect(fixed.getByTestId('write-changed-fields')).toHaveText('None')
    expect(await fixed.getByTestId('write-before').textContent()).toBe(await fixed.getByTestId('write-after').textContent())
  }
})

test('API writes: ownership, tenant, role, and mixed patches are rejected atomically', async ({ page }) => {
  for (const [fixture, changes] of [['owner', 'ownerId'], ['tenant', 'tenantId'], ['role', 'role'], ['mixed', 'displayName, role']]) {
    const { vulnerable, fixed } = await compare(page, fixture)
    await expect(vulnerable.getByTestId('write-changed-fields')).toHaveText(changes)
    await expect(vulnerable.getByTestId('write-rows-changed')).toHaveText('1')
    await expect(fixed.locator('.traversal-outcome')).toHaveText('rejected')
    await expect(fixed.getByTestId('write-changed-fields')).toHaveText('None')
    expect(await fixed.getByTestId('write-before').textContent()).toBe(await fixed.getByTestId('write-after').textContent())
    await expect(fixed.getByTestId('write-after')).toContainText('"displayName": "Ada"')
    await expect(fixed.getByTestId('write-after')).toContainText('"role": "member"')
  }
})

test('API writes: schema failures leave no changes and a new selection clears old evidence', async ({ page }) => {
  for (const fixture of ['invalid-type', 'too-long']) {
    const { vulnerable, fixed } = await compare(page, fixture)
    await expect(vulnerable.locator('.traversal-outcome')).toHaveText('updated')
    await expect(fixed.locator('.traversal-outcome')).toHaveText('rejected')
    await expect(fixed.getByTestId('write-rows-changed')).toHaveText('0')
    expect(await fixed.getByTestId('write-before').textContent()).toBe(await fixed.getByTestId('write-after').textContent())
  }
  await page.getByTestId('write-fixture').selectOption('own')
  await expect(page.getByTestId('write-vulnerable-result').getByTestId('write-after')).toHaveCount(0)
  await expect(page.getByTestId('write-fixed-result').getByTestId('write-after')).toHaveCount(0)
  const { fixed } = await compare(page, 'own')
  await expect(fixed.getByTestId('write-before')).toContainText('"displayName": "Ada"')
  await expect(fixed.locator('.traversal-outcome')).toHaveText('updated')
})
