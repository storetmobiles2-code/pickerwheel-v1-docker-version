// @ts-check
const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './specs',
  fullyParallel: false, // tests share the live dev database - avoid cross-test races
  retries: 0,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL: process.env.PICKERWHEEL_BASE_URL || 'http://localhost:9080',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
