# Playwright UI Verification Recipes

Reference implementations for common verification patterns used with the `testing-guidelines` skill.

--------------------------------------------------------------------------------

## Complete Test Harness Boilerplate
```typescript
import { test, expect } from '@playwright/test';

test.describe('Counter View Verification', () => {
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];
  const failedRequests: string[] = [];
  const httpErrors: string[] = [];

  test.beforeEach(async ({ page }) => {
    // 1. Capture console errors and unhandled exceptions
    page.on('console', msg => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });
    page.on('pageerror', err => pageErrors.push(err.message));

    // 2. Capture network failures and HTTP 400+ responses
    page.on('requestfailed', request => {
      failedRequests.push(`${request.method()} ${request.url()}: ${request.failure()?.errorText}`);
    });
    page.on('response', response => {
      if (response.status() >= 400) {
        httpErrors.push(`${response.status()} ${response.url()}`);
      }
    });

    // 3. Disable animations for stable screenshots
    await page.emulateMedia({ reducedMotion: 'reduce' });
  });

  test.afterEach(async () => {
    // Fail test if any console error, unhandled exception, or failed request occurred
    expect(consoleErrors).toEqual([]);
    expect(pageErrors).toEqual([]);
    expect(failedRequests).toEqual([]);
    expect(httpErrors).toEqual([]);
  });

  test('renders desktop and mobile viewports with zero layout shift', async ({ page }) => {
    // Desktop View
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto('/counters', { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);

    const counterList = page.locator('[data-testid="counters-list"]');
    await expect(counterList).toBeVisible();
    await expect(counterList).toHaveScreenshot('counters-list-desktop.png');

    // Mobile View
    await page.setViewportSize({ width: 390, height: 844 });
    await expect(counterList).toHaveScreenshot('counters-list-mobile.png');
  });
});
```

--------------------------------------------------------------------------------

## Interaction and State Transition Check
```typescript
test('increments counter value and reflects updated state', async ({ page }) => {
  await page.goto('/counters', { waitUntil: 'networkidle' });

  const card = page.locator('[data-testid="counter-card-1"]');
  const valueDisplay = card.locator('[data-testid="counter-value"]');
  const incrementBtn = card.locator('button[aria-label="Increment"]');

  // Verify initial state
  await expect(valueDisplay).toHaveText('0');

  // Trigger state transition
  await incrementBtn.click();

  // Verify updated state and visual diff
  await expect(valueDisplay).toHaveText('1');
  await expect(card).toHaveScreenshot('counter-card-incremented.png');
});
```

--------------------------------------------------------------------------------

## Accessible Name and ARIA Assertion
```typescript
test('asserts accessibility tree semantics and interactive targets', async ({ page }) => {
  await page.goto('/settings');

  // Assert button accessible role and name
  const saveBtn = page.getByRole('button', { name: 'Save Preferences' });
  await expect(saveBtn).toBeVisible();
  await expect(saveBtn).toBeEnabled();

  // Assert modal dialog accessibility attributes
  const dialog = page.getByRole('dialog', { name: 'Confirm Deletion' });
  await expect(dialog).toHaveAttribute('aria-modal', 'true');
});
```
