import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('./auth.js', () => ({ loginWithGoogle: vi.fn() }));

import { loginWithGoogle } from './auth.js';
import LoginPage from './LoginPage.jsx';

// Capture the callback GSI is initialized with so tests can simulate Google
// invoking it with a credential.
let capturedCallback = null;

beforeEach(() => {
  loginWithGoogle.mockReset();
  capturedCallback = null;
  window.location.hash = '';
  window.google = {
    accounts: {
      id: {
        initialize: vi.fn(({ callback }) => {
          capturedCallback = callback;
        }),
        renderButton: vi.fn(),
      },
    },
  };
});

afterEach(() => {
  delete window.google;
  window.location.hash = '';
});

// The landing page has two "Log in / Register" buttons: the header one returns
// to the landing hero, while the hero CTA (.login-cta) enters the login flow.
function clickableLoginCta() {
  return screen
    .getAllByRole('button', { name: 'Log in / Register' })
    .find((btn) => btn.classList.contains('login-cta'));
}

describe('LoginPage', () => {
  it('shows the landing view first', () => {
    render(<LoginPage onLoggedIn={() => {}} />);
    expect(
      screen.getByText('Master math for grades 1–12 and AP with spaced repetition.'),
    ).toBeInTheDocument();
    expect(
      screen.getAllByRole('button', { name: 'Log in / Register' }).length,
    ).toBeGreaterThan(0);
  });

  it('renders the Google button after entering the login view', async () => {
    const user = userEvent.setup();
    render(<LoginPage onLoggedIn={() => {}} />);
    await user.click(clickableLoginCta());

    await waitFor(() =>
      expect(window.google.accounts.id.renderButton).toHaveBeenCalled(),
    );
    expect(screen.getByText('Log in or register to continue')).toBeInTheDocument();
  });

  it('calls onLoggedIn with the user after a successful credential exchange', async () => {
    const onLoggedIn = vi.fn();
    loginWithGoogle.mockResolvedValueOnce({ user: { name: 'Ada' } });
    const user = userEvent.setup();
    render(<LoginPage onLoggedIn={onLoggedIn} />);
    await user.click(clickableLoginCta());
    await waitFor(() => expect(capturedCallback).toBeInstanceOf(Function));

    await capturedCallback({ credential: 'google-jwt' });

    expect(loginWithGoogle).toHaveBeenCalledWith('google-jwt');
    await waitFor(() =>
      expect(onLoggedIn).toHaveBeenCalledWith({ user: { name: 'Ada' } }),
    );
  });

  it('surfaces an error when the credential exchange fails', async () => {
    loginWithGoogle.mockRejectedValueOnce(new Error('bad token'));
    const user = userEvent.setup();
    render(<LoginPage onLoggedIn={() => {}} />);
    await user.click(clickableLoginCta());
    await waitFor(() => expect(capturedCallback).toBeInstanceOf(Function));

    await capturedCallback({ credential: 'x' });

    await screen.findByText('bad token');
  });

  it('returns to the landing view via Back', async () => {
    const user = userEvent.setup();
    render(<LoginPage onLoggedIn={() => {}} />);
    await user.click(clickableLoginCta());
    await screen.findByText('Log in or register to continue');

    await user.click(screen.getByRole('button', { name: 'Back' }));
    expect(
      screen.getAllByRole('button', { name: 'Log in / Register' }).length,
    ).toBeGreaterThan(0);
  });

  it('navigates to the Why Solveki and FAQ pages from the header', async () => {
    const user = userEvent.setup();
    render(<LoginPage onLoggedIn={() => {}} />);

    await user.click(screen.getByRole('button', { name: 'Why Solveki' }));
    expect(screen.getByText('Why Solveki?')).toBeInTheDocument();
    expect(screen.getByText(/324 topics/)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'FAQ' }));
    expect(
      screen.getByText('Frequently asked questions'),
    ).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Solveki' }));
    expect(
      screen.getByText('Master math for grades 1–12 and AP with spaced repetition.'),
    ).toBeInTheDocument();
  });

  it('reflects the current landing view in the URL hash', async () => {
    const user = userEvent.setup();
    render(<LoginPage onLoggedIn={() => {}} />);

    await user.click(screen.getByRole('button', { name: 'Why Solveki' }));
    expect(window.location.hash).toBe('#/why');

    await user.click(screen.getByRole('button', { name: 'FAQ' }));
    expect(window.location.hash).toBe('#/faq');

    // The login flow is entered from the landing hero CTA.
    await user.click(screen.getByRole('button', { name: 'Solveki' }));
    await user.click(clickableLoginCta());
    expect(window.location.hash).toBe('#/login');
  });

  it('opens on the view named in the URL hash', () => {
    window.location.hash = '#/faq';
    render(<LoginPage onLoggedIn={() => {}} />);
    expect(screen.getByText('Frequently asked questions')).toBeInTheDocument();
  });

  it('follows browser hashchange events (back/forward)', async () => {
    render(<LoginPage onLoggedIn={() => {}} />);
    expect(
      screen.getByText('Master math for grades 1–12 and AP with spaced repetition.'),
    ).toBeInTheDocument();

    window.location.hash = '#/why';
    window.dispatchEvent(new Event('hashchange'));
    expect(await screen.findByText('Why Solveki?')).toBeInTheDocument();
  });

  it('returns to the landing page from the header Log in / Register button', async () => {
    const user = userEvent.setup();
    render(<LoginPage onLoggedIn={() => {}} />);

    await user.click(screen.getByRole('button', { name: 'FAQ' }));
    expect(screen.getByText('Frequently asked questions')).toBeInTheDocument();

    const headerLogin = screen
      .getAllByRole('button', { name: 'Log in / Register' })
      .find((btn) => btn.classList.contains('header-login'));
    await user.click(headerLogin);

    expect(
      screen.getByText('Master math for grades 1–12 and AP with spaced repetition.'),
    ).toBeInTheDocument();
  });
});
