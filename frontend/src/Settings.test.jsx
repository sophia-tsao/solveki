import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithClient } from './test-utils.jsx';

vi.mock('./auth.js', () => ({
  logout: vi.fn(),
  deleteAccount: vi.fn(),
}));

import { logout, deleteAccount } from './auth.js';
import Settings from './Settings.jsx';

beforeEach(() => {
  logout.mockReset();
  deleteAccount.mockReset();
});

describe('Settings', () => {
  it('has no questions-per-practice field', () => {
    renderWithClient(<Settings onLoggedOut={() => {}} />);
    expect(screen.queryByText('Questions per practice')).not.toBeInTheDocument();
    expect(screen.queryByRole('spinbutton')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Save' })).not.toBeInTheDocument();
  });
});

describe('Settings — account actions', () => {
  it('logs out and notifies the parent', async () => {
    const onLoggedOut = vi.fn();
    logout.mockResolvedValueOnce({ ok: true });
    const user = userEvent.setup();
    renderWithClient(<Settings onLoggedOut={onLoggedOut} />);

    await user.click(screen.getByRole('button', { name: 'Log out' }));
    await waitFor(() => expect(onLoggedOut).toHaveBeenCalledTimes(1));
  });

  it('requires confirmation before deleting the account', async () => {
    const onLoggedOut = vi.fn();
    deleteAccount.mockResolvedValueOnce({ ok: true });
    const user = userEvent.setup();
    renderWithClient(<Settings onLoggedOut={onLoggedOut} />);

    // First click reveals the confirmation, does not delete.
    await user.click(screen.getByRole('button', { name: 'Delete account' }));
    expect(deleteAccount).not.toHaveBeenCalled();
    await screen.findByText(/This permanently deletes your account/);

    await user.click(screen.getByRole('button', { name: 'Delete permanently' }));
    await waitFor(() => expect(deleteAccount).toHaveBeenCalledTimes(1));
    expect(onLoggedOut).toHaveBeenCalledTimes(1);
  });

  it('cancels the delete confirmation', async () => {
    const user = userEvent.setup();
    renderWithClient(<Settings onLoggedOut={() => {}} />);

    await user.click(screen.getByRole('button', { name: 'Delete account' }));
    await user.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(
      screen.queryByText(/This permanently deletes your account/),
    ).not.toBeInTheDocument();
    expect(deleteAccount).not.toHaveBeenCalled();
  });
});
