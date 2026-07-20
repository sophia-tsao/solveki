import { test, expect } from '@playwright/test';
import { resetUser } from './fixtures.js';

test.describe('settings page', () => {
  test.beforeEach(async ({ page }) => {
    await resetUser(page);
    // Settings starts with default state (useState(10)/'en') that happens to
    // equal the freshly-reset server values, then overwrites the inputs when
    // GET /settings/ resolves. Waiting for a *value* would pass instantly from
    // the defaults and prove nothing, letting the late response clobber what a
    // test types. So wait for the response itself before interacting.
    await Promise.all([
      page.waitForResponse((r) => r.url().includes('/settings/') && r.request().method() === 'GET'),
      page.goto('/#/settings'),
    ]);
  });

  test('loads with defaults', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();
    await expect(page.locator('.settings-select')).toHaveValue('en');
    await expect(page.locator('.settings-input')).toHaveValue('10');
  });

  test('saving changes persists across reload', async ({ page }) => {
    await page.locator('.settings-select').selectOption('es');
    await page.locator('.settings-input').fill('5');
    await page.getByRole('button', { name: 'Save' }).click();
    await expect(page.getByText('Settings saved.')).toBeVisible();

    await page.reload();
    await expect(page.locator('.settings-select')).toHaveValue('es');
    await expect(page.locator('.settings-input')).toHaveValue('5');
  });

  test('rejects a questions-per-day below 1', async ({ page }) => {
    await page.locator('.settings-input').fill('0');
    await page.getByRole('button', { name: 'Save' }).click();
    await expect(page.getByText('Number of questions must be at least 1.')).toBeVisible();
  });

  test('deleting the account returns to the login screen', async ({ page }) => {
    await page.getByRole('button', { name: 'Delete account' }).click();
    await page.getByRole('button', { name: 'Delete permanently' }).click();
    await expect(page.getByRole('button', { name: 'Log in / Register' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Practice' })).toHaveCount(0);
  });
});
