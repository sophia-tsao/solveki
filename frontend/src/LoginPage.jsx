import { useState, useEffect, useRef } from 'react';
import { loginWithGoogle } from './auth.js';
import './LoginPage.css';

const GSI_SRC = 'https://accounts.google.com/gsi/client';
const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

// Load the Google Identity Services script once, resolving when ready.
let gsiPromise = null;
function loadGsi() {
  if (gsiPromise) return gsiPromise;
  gsiPromise = new Promise((resolve, reject) => {
    if (window.google?.accounts?.id) {
      resolve();
      return;
    }
    const script = document.createElement('script');
    script.src = GSI_SRC;
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Failed to load Google sign-in'));
    document.head.appendChild(script);
  });
  return gsiPromise;
}

function LoginPage({ onLoggedIn }) {
  const [view, setView] = useState('landing'); // landing | login
  const [error, setError] = useState(null);
  const buttonRef = useRef(null);

  useEffect(() => {
    if (view !== 'login') return;
    let cancelled = false;

    loadGsi()
      .then(() => {
        if (cancelled) return;
        if (!CLIENT_ID) {
          setError('Google sign-in is not configured (missing VITE_GOOGLE_CLIENT_ID).');
          return;
        }
        window.google.accounts.id.initialize({
          client_id: CLIENT_ID,
          callback: async (response) => {
            try {
              const data = await loginWithGoogle(response.credential);
              onLoggedIn(data.user);
            } catch (err) {
              setError(err.message);
            }
          },
        });
        window.google.accounts.id.renderButton(buttonRef.current, {
          theme: 'outline',
          size: 'large',
          text: 'continue_with',
          shape: 'pill',
        });
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      });

    return () => { cancelled = true; };
  }, [view, onLoggedIn]);

  if (view === 'landing') {
    return (
      <div className="login-page">
        <h1 className="login-brand">Solveki</h1>
        <button className="login-cta" onClick={() => setView('login')}>
          Log in / Register
        </button>
      </div>
    );
  }

  return (
    <div className="login-page">
      <h1 className="login-brand">Solveki</h1>
      <p className="login-subtitle">Log in or register to continue</p>
      <div ref={buttonRef} className="login-google-button" />
      {error && <p className="login-error">{error}</p>}
      <button className="login-back" onClick={() => { setError(null); setView('landing'); }}>
        Back
      </button>
    </div>
  );
}

export default LoginPage;
