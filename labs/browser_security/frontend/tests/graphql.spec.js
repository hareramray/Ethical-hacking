import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-graphql').click()
})

const resultPanel = (page, mode) => page.getByTestId(`graphql-${mode}-result`)
const readJSON = async (panel, field) => JSON.parse(await panel.getByTestId(`graphql-${field}`).innerText())

async function compare(page, fixture) {
  await page.getByTestId('graphql-fixture').selectOption(fixture)
  const pending = page.waitForResponse(response => response.url().includes('/api/graphql/compare/') && response.request().method() === 'POST')
  await page.getByTestId('graphql-run').click()
  const response = await pending
  expect(response.status()).toBe(200)
  expect(response.request().postDataJSON()).toEqual({ fixture })
  await expect(resultPanel(page, 'fixed').getByTestId('graphql-data')).toBeVisible()
  await expect(page.getByTestId('graphql-run')).toBeEnabled()
  const body = await response.json()
  for (const mode of ['vulnerable', 'fixed']) {
    expect(await readJSON(resultPanel(page, mode), 'data')).toEqual(body.results[mode].data)
    expect(await readJSON(resultPanel(page, mode), 'errors')).toEqual(body.results[mode].errors)
  }
  return body.results
}

test('allowed query returns the actual synthetic marker in both GraphQL responses', async ({ page }) => {
  const results = await compare(page, 'allowed')
  for (const mode of ['vulnerable', 'fixed']) {
    expect(results[mode].data).toEqual({ document: { id: 'blue-note', title: 'Blue notebook', marker: 'FICTIONAL_BLUE_MARKER' } })
    expect(results[mode].errors).toEqual([])
    await expect(resultPanel(page, mode).getByTestId('graphql-resolver-calls')).toHaveText('4')
  }
})

test('nested cross-tenant relation returns partial fixed data and a path-specific error', async ({ page }) => {
  const results = await compare(page, 'nested-tenant')
  expect(results.vulnerable.data.document.relatedDocument.marker).toBe('FICTIONAL_AMBER_MARKER')
  expect(results.fixed.data).toEqual({ document: { id: 'blue-note', relatedDocument: null } })
  expect(results.fixed.errors[0]).toMatchObject({ path: ['document', 'relatedDocument'], extensions: { code: 'FORBIDDEN' } })
  await expect(resultPanel(page, 'fixed').getByTestId('graphql-data')).not.toContainText('FICTIONAL_AMBER_MARKER')
})

test('protected field is null while the allowed title survives', async ({ page }) => {
  const results = await compare(page, 'protected-field')
  expect(results.vulnerable.data.document.adminNote).toBe('FICTIONAL_BLUE_ADMIN_NOTE')
  expect(results.fixed.data.document).toEqual({ id: 'blue-note', title: 'Blue notebook', adminNote: null })
  expect(results.fixed.errors[0].path).toEqual(['document', 'adminNote'])
})

test('allowed own-document mutation performs one real isolated write in each mode', async ({ page }) => {
  const results = await compare(page, 'own-mutation')
  for (const mode of ['vulnerable', 'fixed']) {
    expect(results[mode].data.renameDocument.title).toBe('HARMLESS_RENAMED_NOTE')
    expect(results[mode].before['blue-note']).toBe('Blue notebook')
    expect(results[mode].after['blue-note']).toBe('HARMLESS_RENAMED_NOTE')
    expect(results[mode].errors).toEqual([])
    await expect(resultPanel(page, mode).getByTestId('graphql-writes')).toHaveText('1')
  }
})

test('forbidden mutation leaves the fixed store unchanged despite HTTP success', async ({ page }) => {
  const results = await compare(page, 'forbidden-mutation')
  expect(results.vulnerable.after['amber-note']).toBe('HARMLESS_RENAMED_NOTE')
  expect(results.fixed.data).toEqual({ renameDocument: null })
  expect(results.fixed.errors[0].extensions.code).toBe('FORBIDDEN')
  expect(results.fixed.after).toEqual(results.fixed.before)
  for (const mode of ['vulnerable', 'fixed']) {
    const panel = resultPanel(page, mode)
    expect(await readJSON(panel, 'before')).toEqual(results[mode].before)
    expect(await readJSON(panel, 'after')).toEqual(results[mode].after)
    await expect(panel.getByTestId('graphql-writes')).toHaveText(mode === 'vulnerable' ? '1' : '0')
  }
})

test('aliases preserve allowed results and independently refuse foreign documents', async ({ page }) => {
  const results = await compare(page, 'aliases')
  expect(results.vulnerable.data.other.marker).toBe('FICTIONAL_AMBER_MARKER')
  expect(results.fixed.data).toEqual({ own: { id: 'blue-note', marker: 'FICTIONAL_BLUE_MARKER' }, other: null })
  expect(results.fixed.errors[0].path).toEqual(['other'])
  expect(results.fixed.checks.map(check => check.path)).toEqual([['own'], ['other']])
})

test('field-budget validation refuses bounded fan-out before executing any resolver', async ({ page }) => {
  const results = await compare(page, 'query-budget')
  expect(Object.keys(results.vulnerable.data)).toHaveLength(8)
  expect(results.fixed.data).toBeNull()
  expect(results.fixed.errors[0].extensions.code).toBe('FIELD_BUDGET_EXCEEDED')
  expect(results.fixed.checks).toEqual([])
  await expect(resultPanel(page, 'fixed').getByTestId('graphql-validation')).toHaveText('No')
  await expect(resultPanel(page, 'fixed').getByTestId('graphql-field-count')).toHaveText('24')
  await expect(resultPanel(page, 'fixed').getByTestId('graphql-resolver-calls')).toHaveText('0')
  await expect(resultPanel(page, 'vulnerable').getByTestId('graphql-resolver-calls')).toHaveText('24')
})

test('selecting a new fixture clears evidence and reruns start with fresh titles', async ({ page }) => {
  await compare(page, 'own-mutation')
  await page.getByTestId('graphql-fixture').selectOption('forbidden-mutation')
  await expect(resultPanel(page, 'fixed').getByTestId('graphql-data')).toHaveCount(0)
  const results = await compare(page, 'forbidden-mutation')
  expect(results.vulnerable.before).toEqual({ 'blue-note': 'Blue notebook', 'amber-note': 'Amber notebook' })
  expect(results.fixed.before).toEqual(results.vulnerable.before)
  await compare(page, 'allowed')
  await expect(resultPanel(page, 'fixed').getByTestId('graphql-data')).toContainText('Blue notebook')
})

test('malformed evidence is rejected without rendering failure and retry works', async ({ page }) => {
  const failures = []
  page.on('pageerror', error => failures.push(error.message))
  await page.route('**/api/graphql/compare/', async route => {
    const response = await route.fetch()
    const data = await response.json()
    data.results.fixed.checks = null
    await route.fulfill({ response, json: data })
  })
  await page.getByTestId('graphql-run').click()
  await expect(page.getByRole('alert')).toHaveText('The server returned an unexpected GraphQL comparison.')
  expect(failures).toEqual([])
  await expect(resultPanel(page, 'fixed').getByTestId('graphql-data')).toHaveCount(0)
  await page.unroute('**/api/graphql/compare/')
  await compare(page, 'allowed')
})

test('leaving the tab aborts pending comparison and cannot restore stale evidence', async ({ page }) => {
  let release, markEntered
  const entered = new Promise(resolve => { markEntered = resolve })
  const gate = new Promise(resolve => { release = resolve })
  await page.route('**/api/graphql/compare/', async route => {
    const response = await route.fetch()
    markEntered()
    await gate
    try { await route.fulfill({ response }) } catch { /* The component aborted the request. */ }
  })
  await page.getByTestId('graphql-run').click()
  await entered
  await page.getByTestId('nav-xss').click()
  release()
  await page.getByTestId('nav-graphql').click()
  await expect(resultPanel(page, 'fixed').getByTestId('graphql-data')).toHaveCount(0)
  await expect(page.getByTestId('graphql-run')).toBeEnabled()
})
