import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithClient } from './test-utils.jsx';

// App is pure shell/routing: it gates on the ['me'] session query, then renders
// a page based on the URL hash. The page bodies and the network layer are
// irrelevant here, so every child is stubbed to a marker and fetchMe is scripted.
// The Header stub exposes buttons that drive linkClicked, and the Settings stub
// exposes onLoggedOut, so navigation and logout can be exercised end to end.
vi.mock('./auth.js', () => ({ fetchMe: vi.fn() }));
vi.mock('./logger.js', () => ({
  createLogger: () => ({ debug() {}, info() {}, warn() {}, error() {} }),
}));
vi.mock('./MathProblem.jsx', () => ({ default: () => <div>math-page</div> }));
vi.mock('./Dashboard.jsx', () => ({ default: () => <div>dashboard-page</div> }));
vi.mock('./CourseList.jsx', () => ({ default: () => <div>courses-page</div> }));
vi.mock('./Settings.jsx', () => ({
  default: ({ onLoggedOut }) => (
    <div>
      settings-page
      <button onClick={onLoggedOut}>do-logout</button>
    </div>
  ),
}));
vi.mock('./LoginPage.jsx', () => ({
  default: ({ onLoggedIn }) => (
    <div>
      login-page
      <button onClick={() => onLoggedIn({ name: 'Ada' })}>do-login</button>
    </div>
  ),
}));
vi.mock('./Header.jsx', () => ({
  default: ({ currentPage, linkClicked }) => (
    <div>
      <span>header-on-{currentPage}</span>
      {['math', 'dashboard', 'courses', 'settings'].map((p) => (
        <button key={p} onClick={() => linkClicked(p)}>
          go-{p}
        </button>
      ))}
    </div>
  ),
}));

import { fetchMe } from './auth.js';
import App from './App.jsx';

const AUTHED = { authenticated: true, user: { name: 'Ada' } };
const ANON = { authenticated: false };

beforeEach(() => {
  fetchMe.mockReset();
  window.location.hash = '';
});

afterEach(() => {
  window.location.hash = '';
});

describe('App — auth gate', () => {
  it('shows the login page when there is no active session', async () => {
    fetchMe.mockResolvedValue(ANON);
    renderWithClient(<App />);
    expect(await screen.findByText('login-page')).toBeInTheDocument();
    expect(screen.queryByText(/header-on/)).not.toBeInTheDocument();
  });

  it('shows the app shell once authenticated', async () => {
    fetchMe.mockResolvedValue(AUTHED);
    renderWithClient(<App />);
    expect(await screen.findByText('header-on-math')).toBeInTheDocument();
    expect(screen.getByText('math-page')).toBeInTheDocument();
  });

  it('falls back to logged-out when the session check fails', async () => {
    fetchMe.mockRejectedValue(new Error('offline'));
    renderWithClient(<App />);
    expect(await screen.findByText('login-page')).toBeInTheDocument();
  });

  it('renders the app after a successful login writes the session', async () => {
    fetchMe.mockResolvedValue(ANON);
    const user = userEvent.setup();
    renderWithClient(<App />);
    await user.click(await screen.findByText('do-login'));
    expect(await screen.findByText('header-on-math')).toBeInTheDocument();
  });
});

describe('App — routing', () => {
  it('opens on the page named in the URL hash', async () => {
    window.location.hash = '#/settings';
    fetchMe.mockResolvedValue(AUTHED);
    renderWithClient(<App />);
    expect(await screen.findByText('settings-page')).toBeInTheDocument();
  });

  it('defaults to the math page for an unknown hash', async () => {
    window.location.hash = '#/bogus';
    fetchMe.mockResolvedValue(AUTHED);
    renderWithClient(<App />);
    expect(await screen.findByText('math-page')).toBeInTheDocument();
  });

  it('switches pages when the header requests navigation', async () => {
    fetchMe.mockResolvedValue(AUTHED);
    const user = userEvent.setup();
    renderWithClient(<App />);
    await screen.findByText('math-page');

    await user.click(screen.getByText('go-dashboard'));
    expect(screen.getByText('dashboard-page')).toBeInTheDocument();
    expect(window.location.hash).toBe('#/dashboard');
  });

  it('follows browser hashchange events (back/forward)', async () => {
    fetchMe.mockResolvedValue(AUTHED);
    renderWithClient(<App />);
    await screen.findByText('math-page');

    act(() => {
      window.location.hash = '#/courses';
      window.dispatchEvent(new Event('hashchange'));
    });
    expect(await screen.findByText('courses-page')).toBeInTheDocument();
  });
});

describe('App — logout', () => {
  it('returns to the login page and resets the hash to math', async () => {
    window.location.hash = '#/settings';
    fetchMe.mockResolvedValue(AUTHED);
    const user = userEvent.setup();
    renderWithClient(<App />);

    await user.click(await screen.findByText('do-logout'));
    expect(await screen.findByText('login-page')).toBeInTheDocument();
    expect(window.location.hash).toBe('#/math');
  });
});
