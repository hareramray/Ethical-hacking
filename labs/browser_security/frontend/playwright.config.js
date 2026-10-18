import { defineConfig } from '@playwright/test'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const frontendDir = path.dirname(fileURLToPath(import.meta.url))
const labDir = path.resolve(frontendDir, '..')
const python = path.join(labDir, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python')
const channel = process.env.LAB_BROWSER_CHANNEL

export default defineConfig({
  testDir: './tests',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: true,
  workers: 2,
  reporter: 'list',
  use: {
    baseURL: 'http://127.0.0.1:8766',
    browserName: 'chromium',
    ...(channel ? { channel } : {}),
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: `"${python}" "${path.join(labDir, 'run_lab.py')}" --serve --port 8766`,
    url: 'http://127.0.0.1:8766/api/health',
    timeout: 60_000,
    reuseExistingServer: false,
    env: { LAB_DATA_DIR: path.join(labDir, '.test-data') },
  },
})
