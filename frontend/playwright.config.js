import { defineConfig, devices } from '@playwright/test';

// End-to-end config. Tests drive a real browser against the built SPA, which in
// turn talks to a live Django backend.
//
// - The frontend is served by `vite preview` (built with VITE_API_URL baked in);
//   Playwright starts and stops it via `webServer` below.
// - The backend is expected to already be running at API_URL with
//   ENABLE_TEST_LOGIN=1 (see README "End-to-end tests"). CI starts it; locally
//   you start it in another terminal.
// - global-setup.js logs in once via /auth/test-login/ and saves the session
//   cookie to STORAGE_STATE, so every test starts authenticated.

// Preview runs on 5173 to match the backend's CORS_ALLOWED_ORIGINS (the only
// origin allowed to send credentialed requests). See config/settings.py.
const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173';
const API_URL = process.env.E2E_API_URL || 'http://localhost:8000';

export const STORAGE_STATE = './e2e/.auth/state.json';

export default defineConfig({
  testDir: './e2e',
  // The whole suite shares one backend user (the E2E test user), and each test
  // resets that user's state via /auth/test-login/. Running tests in parallel
  // would let one test wipe another's selections/deck/settings mid-flight, so
  // the suite runs serially with a single worker.
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? [['html'], ['github']] : 'list',

  // Passed to global-setup.js, which needs the backend URL to log in.
  globalSetup: './e2e/global-setup.js',

  use: {
    baseURL: BASE_URL,
    storageState: STORAGE_STATE,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // Build and serve the SPA with the backend URL baked in. Reuses an already
  // running preview server locally so re-runs are fast.
  webServer: {
    command: `npm run build && npm run preview -- --port 5173 --strictPort`,
    url: BASE_URL,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    env: {
      VITE_API_URL: API_URL,
    },
  },
});
