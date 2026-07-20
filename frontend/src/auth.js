// Small helpers for talking to the auth-protected backend.
//
// All requests use `credentials: 'include'` so the Django session cookie is
// sent cross-origin (Vite dev server on :5173 -> Django on :8000).

import { createLogger } from './logger.js';

const log = createLogger('api');

const API_URL = import.meta.env.VITE_API_URL;

// The client's local calendar day as YYYY-MM-DD. Deck endpoints take this as a
// `today` query param so the daily deck resets at the user's local midnight,
// not the server's UTC midnight (the backend clock runs in UTC). Any request
// that can mutate today's deck (deck load/advance, topic selection, settings)
// must send it so the whole set agrees on which day's deck it's touching.
export function localDay() {
  return new Date().toLocaleDateString('en-CA');
}

export async function apiFetch(path, options = {}) {
  const method = options.method || 'GET';
  log.debug(`${method} ${path}`);
  try {
    const res = await fetch(`${API_URL}${path}`, { credentials: 'include', ...options });
    if (!res.ok) {
      log.warn(`${method} ${path} -> ${res.status}`);
    }
    return res;
  } catch (err) {
    // Network-level failure (server down, CORS, offline) — never reaches the
    // status check above, so log it here.
    log.error(`${method} ${path} failed:`, err.message);
    throw err;
  }
}

export async function fetchMe() {
  const res = await apiFetch('/auth/me/');
  if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
  return res.json();
}

export async function loginWithGoogle(credential) {
  const res = await apiFetch('/auth/google/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ credential }),
  });
  const data = await res.json();
  if (!res.ok) {
    log.error('Google login failed:', data.error || res.status);
    throw new Error(data.error || `HTTP error! Status: ${res.status}`);
  }
  log.info('Google login succeeded');
  return data;
}

export async function logout() {
  const res = await apiFetch('/auth/logout/', { method: 'POST' });
  if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
  log.info('Logged out');
  return res.json();
}

export async function deleteAccount() {
  const res = await apiFetch('/auth/delete/', { method: 'DELETE' });
  if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
  log.info('Account deleted');
  return res.json();
}
