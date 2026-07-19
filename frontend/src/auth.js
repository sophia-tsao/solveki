// Small helpers for talking to the auth-protected backend.
//
// All requests use `credentials: 'include'` so the Django session cookie is
// sent cross-origin (Vite dev server on :5173 -> Django on :8000).

const API_URL = import.meta.env.VITE_API_URL;

export function apiFetch(path, options = {}) {
  return fetch(`${API_URL}${path}`, { credentials: 'include', ...options });
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
  if (!res.ok) throw new Error(data.error || `HTTP error! Status: ${res.status}`);
  return data;
}

export async function logout() {
  const res = await apiFetch('/auth/logout/', { method: 'POST' });
  if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
  return res.json();
}

export async function deleteAccount() {
  const res = await apiFetch('/auth/delete/', { method: 'DELETE' });
  if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
  return res.json();
}
