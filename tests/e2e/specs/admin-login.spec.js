// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * Only the failure path is covered here deliberately - a real login
 * needs the live admin password, which this suite does not have and
 * should not embed even for testing (same boundary the rest of this
 * project's automated work has respected all along). The happy-path
 * login flow itself is a single fetch + two style.display toggles
 * (see login() in admin.html) and was verified by direct code reading
 * instead.
 */

test('wrong admin password shows an error and never reveals admin content', async ({ page }) => {
  await page.goto('/admin.html');
  await expect(page.locator('#loginSection')).toBeVisible();
  await expect(page.locator('#adminContent')).not.toHaveClass(/show/);

  await page.fill('#adminPassword', 'definitely-not-the-real-password');
  await page.click('button:has-text("Login")');

  await expect(page.locator('#loginError')).toHaveText(/invalid password/i);
  await expect(page.locator('#loginSection')).toBeVisible();
  await expect(page.locator('#adminContent')).not.toHaveClass(/show/);
});

test('empty password does not crash the login flow', async ({ page }) => {
  await page.goto('/admin.html');
  await page.click('button:has-text("Login")');
  await expect(page.locator('#loginError')).not.toBeEmpty();
  await expect(page.locator('#adminContent')).not.toHaveClass(/show/);
});
