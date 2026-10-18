import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Browsers without FedCM fall back to Google's sign-in popup, which has to
// talk back to this page. The default COOP severs that link; allow-popups keeps
// it. Mirrored for production in vercel.json.
const COOP_HEADERS = { 'Cross-Origin-Opener-Policy': 'same-origin-allow-popups' }

export default defineConfig({
  plugins: [react()],
  server: { headers: COOP_HEADERS },
  preview: { headers: COOP_HEADERS },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      input: 'index.html',
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.js',
    css: false,
    // Pin env vars the components read at module load so tests never depend on
    // a local .env. CI has no .env, which would otherwise change behaviour
    // (e.g. LoginPage falls back to its "not configured" branch).
    env: {
      VITE_API_URL: 'http://testserver',
      VITE_GOOGLE_CLIENT_ID: 'test-client-id',
    },
    // Playwright specs live in e2e/ and run via `npm run test:e2e`, not vitest.
    exclude: ['e2e/**', 'node_modules/**', 'dist/**'],
  },
})
