import { request } from '@playwright/test';
import { STORAGE_STATE } from '../playwright.config.js';

const API_URL = process.env.E2E_API_URL || 'http://localhost:8000';

// Log in once before the suite and persist the session cookie.
//
// The SPA authenticates by POSTing to /auth/test-login/ (a backend endpoint
// gated behind ENABLE_TEST_LOGIN) and relying on the returned Django session
// cookie for subsequent credentialed requests. We do the same here with an API
// request context, then save its cookies to STORAGE_STATE so every test starts
// with an authenticated session — no repeated login, no Google OAuth.
export default async function globalSetup() {
  const context = await request.newContext({ baseURL: API_URL });
  const res = await context.post('/auth/test-login/');
  if (!res.ok()) {
    throw new Error(
      `Test login failed (${res.status()}). Is the backend running at ${API_URL} ` +
        `with ENABLE_TEST_LOGIN=1? See README "End-to-end tests".`,
    );
  }
  await context.storageState({ path: STORAGE_STATE });
  await context.dispose();
}
