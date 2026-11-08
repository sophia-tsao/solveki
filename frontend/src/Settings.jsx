import { useState } from 'react';
import './Settings.css';
import { logout, deleteAccount } from './auth.js';
import { createLogger } from './logger.js';

const log = createLogger('settings');

function Settings({ onLoggedOut }) {
  const [error, setError] = useState(null);
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  const handleLogout = async () => {
    setError(null);
    try {
      await logout();
      onLoggedOut();
    } catch (err) {
      log.error('Logout failed:', err.message);
      setError(err.message);
    }
  };

  const handleDeleteAccount = async () => {
    setError(null);
    try {
      await deleteAccount();
      onLoggedOut();
    } catch (err) {
      log.error('Account deletion failed:', err.message);
      setError(err.message);
    }
  };

  return (
    <div className="settings-card">
      <h2 className="settings-title">Settings</h2>

      {error && <p className="settings-error">Error: {error}</p>}

      <div className="settings-account">
        <span className="settings-label">Account</span>
        <button className="settings-logout" onClick={handleLogout}>Log out</button>

        {confirmingDelete ? (
          <div className="settings-delete-confirm">
            <p className="settings-delete-warning">
              This permanently deletes your account and all your data. This cannot be undone.
            </p>
            <div className="settings-delete-actions">
              <button className="settings-delete-cancel" onClick={() => setConfirmingDelete(false)}>
                Cancel
              </button>
              <button className="settings-delete" onClick={handleDeleteAccount}>
                Delete permanently
              </button>
            </div>
          </div>
        ) : (
          <button className="settings-delete" onClick={() => setConfirmingDelete(true)}>
            Delete account
          </button>
        )}
      </div>
    </div>
  );
}

export default Settings;
