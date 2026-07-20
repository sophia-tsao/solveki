import { test, expect } from '@playwright/test';
import { resetUser } from './fixtures.js';

test.describe('authentication gate', () => {
  test.beforeEach(async ({ page }) => {
    await resetUser(page);
  });

  test('authenticated user lands on the Practice page', async ({ page }) => {
    await page.goto('/');
    // The header nav only renders when logged in.
    await expect(page.getByRole('button', { name: 'Practice' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Available Courses' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Settings' })).toBeVisible();
  });

  test('logging out returns to the login screen', async ({ page }) => {
    await page.goto('/#/settings');
    await page.getByRole('button', { name: 'Log out' }).click();
    // Landing page: brand + the login CTA, and no header nav.
    await expect(page.getByRole('button', { name: 'Log in / Register' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Practice' })).toHaveCount(0);
  });
});

test.describe('unauthenticated visitor', () => {
  // Fresh context with no saved session cookie.
  test.use({ storageState: { cookies: [], origins: [] } });

  test('sees the landing page, not the app', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Solveki' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Log in / Register' })).toBeVisible();
    // No app nav for anonymous users.
    await expect(page.getByRole('button', { name: 'Practice' })).toHaveCount(0);
  });

  test('the login CTA reveals the Google sign-in view', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Log in / Register' }).click();
    await expect(page.getByText('Log in or register to continue')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Back' })).toBeVisible();
  });
});
