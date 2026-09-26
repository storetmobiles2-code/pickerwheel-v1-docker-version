// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * These run against a live, already-running PickerWheel instance (the
 * docker-compose dev stack) - not an isolated test database like the
 * backend pytest suite. A real spin here consumes real inventory, same
 * as a real customer would. Designed to be resilient to whatever
 * prizes/inventory currently exist rather than asserting exact counts.
 */

test.describe('Customer wheel page - happy path', () => {
  test('loads with the wheel rendered and centered, in Neon by default', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('#wheel')).toBeVisible();
    const segmentCount = await page.locator('.wheel-inner path').count();
    expect(segmentCount).toBeGreaterThan(0);
    expect(await page.evaluate(() => document.documentElement.dataset.designMode)).toBe('neon');
  });

  test('How It Works floats bottom-right on desktop and does not overlap the wheel', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('/');
    const howItWorks = page.locator('.how-it-works');
    const wheel = page.locator('#wheel');
    await expect(howItWorks).toBeVisible();

    const [hiwBox, wheelBox] = await Promise.all([
      howItWorks.boundingBox(),
      wheel.boundingBox(),
    ]);
    // Floating card sits to the right of the wheel with no horizontal overlap
    expect(hiwBox.x).toBeGreaterThan(wheelBox.x + wheelBox.width);
    expect(await howItWorks.evaluate(el => getComputedStyle(el).position)).toBe('fixed');
  });

  test('How It Works reverts to a static stacked card on a narrow viewport', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/');
    const howItWorks = page.locator('.how-it-works');
    await expect(howItWorks).toBeVisible();
    expect(await howItWorks.evaluate(el => getComputedStyle(el).position)).toBe('static');
  });

  test('spinning the wheel awards a prize and shows the result modal', async ({ page }) => {
    await page.goto('/');
    await page.click('#spinButton');

    // pre-spin -> animate -> spin -> modal is a multi-second sequence
    await expect(page.locator('#modalOverlay')).toHaveClass(/show/, { timeout: 20000 });
    const prizeName = await page.locator('#prizeName').textContent();
    expect(prizeName.trim().length).toBeGreaterThan(0);

    await page.click('#closeModal');
    await expect(page.locator('#modalOverlay')).not.toHaveClass(/show/);
  });

  test('sound and effects toggles persist across a reload', async ({ page }) => {
    await page.goto('/');
    await page.click('#soundToggle');
    await expect(page.locator('#soundToggle')).toHaveClass(/disabled/);

    await page.reload();
    await expect(page.locator('#soundToggle')).toHaveClass(/disabled/);

    // restore default state so this test doesn't affect others sharing
    // the same browser storage
    await page.click('#soundToggle');
    await expect(page.locator('#soundToggle')).not.toHaveClass(/disabled/);
  });

  test('design mode toggle switches to Material and persists across reload', async ({ page }) => {
    await page.goto('/');
    await page.click('#designModeToggle');
    await expect.poll(
      () => page.evaluate(() => document.documentElement.dataset.designMode)
    ).toBe('material');

    await page.reload();
    expect(await page.evaluate(() => document.documentElement.dataset.designMode)).toBe('material');

    // restore default for other tests
    await page.click('#designModeToggle');
    await expect.poll(
      () => page.evaluate(() => document.documentElement.dataset.designMode)
    ).toBe('neon');
  });
});

test.describe('Customer wheel page - failure path', () => {
  test('spin request for a prize that is out of stock shows an error, not a crash', async ({ page }) => {
    await page.goto('/');
    // Force the finalize call to reference a prize id that cannot
    // possibly have stock, bypassing the wheel's own selection so we
    // can deterministically hit the backend's rejection path.
    const result = await page.evaluate(async () => {
      const resp = await fetch('/api/spin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'e2e-failure-test', prize_id: 999999 }),
      });
      return { status: resp.status, body: await resp.json() };
    });
    expect(result.status).toBe(400);
    expect(result.body.success).toBe(false);
    expect(typeof result.body.error).toBe('string');
  });
});
