import { test, expect } from '@playwright/test';
import { resetUser } from './fixtures.js';

test.describe('settings page', () => {
  test.beforeEach(async ({ page }) => {
    await resetUser(page);
    await page.goto('/#/settings');
  });

  test('loads without a questions-per-practice field', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();
    await expect(page.getByText('Questions per practice')).toHaveCount(0);
  });

  test('deleting the account returns to the login screen', async ({ page }) => {
    await page.getByRole('button', { name: 'Delete account' }).click();
    await page.getByRole('button', { name: 'Delete permanently' }).click();
    // Landing page has two "Log in / Register" buttons; scope to the hero CTA.
    await expect(
      page.getByRole('main').getByRole('button', { name: 'Log in / Register' })
    ).toBeVisible();
    await expect(page.getByRole('button', { name: 'Practice' })).toHaveCount(0);
  });
});
