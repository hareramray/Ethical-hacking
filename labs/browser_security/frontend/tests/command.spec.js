import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('app-ready')).toBeVisible()
  await page.getByTestId('nav-command').click()
})

async function compare(page, fixture) {
  await page.getByTestId('command-fixture').selectOption(fixture)
  await page.getByTestId('command-run').click()
  await expect(page.getByTestId('command-run')).toBeEnabled()
  const vulnerable = page.getByTestId('command-vulnerable-result')
  const fixed = page.getByTestId('command-fixed-result')
  for (const result of [vulnerable, fixed]) await expect(result.locator('.traversal-outcome')).toHaveText('completed')
  return { vulnerable, fixed }
}

test('command: ordinary names complete without marker actions in both handlers', async ({ page }) => {
  const { vulnerable, fixed } = await compare(page, 'normal')
  for (const result of [vulnerable, fixed]) await expect(result.getByTestId('command-effect')).toHaveText('No: no marker action')
  await expect(vulnerable.getByTestId('command-stdout')).toHaveText('Alice')
  const recorded = JSON.parse(await fixed.getByTestId('command-stdout').textContent())
  expect(recorded).toEqual({ argv: ['--', 'Alice'], names: ['Alice'], flag: false, marker: null })
})

test('command: a shell separator prints a marker only in the vulnerable process', async ({ page }) => {
  const { vulnerable, fixed } = await compare(page, 'separator')
  await expect(vulnerable.getByTestId('command-effect')).toHaveText('Yes: marker action ran')
  expect((await vulnerable.getByTestId('command-stdout').textContent()).split(/\r?\n/)).toContain('COMMAND_SEPARATOR_MARKER')
  await expect(fixed.getByTestId('command-effect')).toHaveText('No: no marker action')
  const input = await page.getByTestId('command-input').textContent()
  const recorded = JSON.parse(await fixed.getByTestId('command-stdout').textContent())
  expect(recorded).toEqual({ argv: ['--', input], names: [input], flag: false, marker: null })
  await compare(page, 'normal')
  await expect(vulnerable.getByTestId('command-stdout')).not.toContainText('COMMAND_SEPARATOR_MARKER')
})

test('command: argument splitting and a leading option differ from literal operands', async ({ page }) => {
  for (const [fixture, input] of [['argument', 'Alice --flag'], ['leading-option', '--flag']]) {
    const { vulnerable, fixed } = await compare(page, fixture)
    await expect(vulnerable.getByTestId('command-effect')).toHaveText('Yes: marker action ran')
    const vulnerableData = JSON.parse(await vulnerable.getByTestId('command-stdout').textContent())
    expect(vulnerableData.flag).toBe(true)
    expect(vulnerableData.marker).toBe('ARGUMENT_FLAG_MARKER')
    await expect(fixed.getByTestId('command-effect')).toHaveText('No: no marker action')
    const fixedData = JSON.parse(await fixed.getByTestId('command-stdout').textContent())
    expect(fixedData).toEqual({ argv: ['--', input], names: [input], flag: false, marker: null })
  }
})
