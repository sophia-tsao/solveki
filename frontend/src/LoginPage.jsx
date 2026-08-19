import { useState, useEffect, useRef } from 'react';
import { loginWithGoogle } from './auth.js';
import { createLogger } from './logger.js';
import './Header.css';
import './LoginPage.css';

const log = createLogger('login');

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

// Public marketing header, formatted like the in-app Header the user sees
// after logging in. Lets visitors move between the landing, "How it works",
// and FAQ pages before authenticating.
function LandingHeader({ view, onNavigate }) {
  return (
    <header className="header">
      <button
        className="header-logo header-logo-button"
        onClick={() => onNavigate('landing')}
      >
        Solveki
      </button>
      <nav className="header-nav">
        <button
          className={view === 'how' ? 'active' : ''}
          onClick={() => onNavigate('how')}
        >
          How it works
        </button>
        <button
          className={view === 'faq' ? 'active' : ''}
          onClick={() => onNavigate('faq')}
        >
          FAQ
        </button>
        <button
          className={view === 'landing' ? 'header-login active' : 'header-login'}
          onClick={() => onNavigate('landing')}
        >
          Log in / Register
        </button>
      </nav>
    </header>
  );
}

function HowItWorks() {
  return (
    <section className="landing-content">
      <h1>How Solveki works</h1>
      <p>
        Solveki helps you commit math skills to long-term memory using{' '}
        <strong>spaced repetition</strong>. Instead of cramming, you review each
        topic at the moment you're most likely to forget it.
      </p>
      <div className="landing-features">
        <div className="landing-feature">
          <h2>The SM-2 algorithm</h2>
          <p>
            Every review is scheduled by the proven SM-2 spaced-repetition
            algorithm. Topics you find easy come back after longer and longer
            gaps, while the ones you struggle with return sooner &mdash; so you
            spend your time exactly where it counts.
          </p>
        </div>
        <div className="landing-feature">
          <h2>Randomly generated problems</h2>
          <p>
            Each topic generates a fresh problem every time, with new numbers
            and setups. You practice the concept and the skill itself, never a
            memorized answer to a single question.
          </p>
        </div>
        <div className="landing-feature">
          <h2>Grades 1&ndash;12, and beyond</h2>
          <p>
            Choose from <strong>324 topics</strong> spanning grades 1 through
            12, including AP courses &mdash; from early arithmetic and fractions
            all the way through algebra, geometry, statistics, precalculus, and
            AP Calculus.
          </p>
        </div>
      </div>
    </section>
  );
}

function Faq() {
  const items = [
    {
      q: 'What is spaced repetition?',
      a: 'Spaced repetition schedules your reviews at growing intervals timed to just before you would forget. It is one of the most effective ways to build durable, long-term memory.',
    },
    {
      q: 'What is SM-2?',
      a: 'SM-2 is the spaced-repetition algorithm Solveki uses to decide when each topic should come back. Based on how well you answer, it adjusts the interval before you see that topic again.',
    },
    {
      q: 'Which topics can I practice?',
      a: 'Solveki offers 324 topics across grades 1 through 12, including AP courses — covering arithmetic, pre-algebra, algebra, geometry, statistics, precalculus, and AP Calculus.',
    },
    {
      q: 'Are the problems the same every time?',
      a: 'No. Every problem is randomly generated, so you always get fresh numbers and setups. This means you learn the underlying skill rather than memorizing specific answers.',
    },
    {
      q: 'How much does it cost?',
      a: 'Sign in with your Google account to get started. Your progress and review schedule are saved so you can pick up right where you left off.',
    },
  ];
  return (
    <section className="landing-content">
      <h1>Frequently asked questions</h1>
      <dl className="landing-faq">
        {items.map(({ q, a }) => (
          <div key={q} className="landing-faq-item">
            <dt>{q}</dt>
            <dd>{a}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function LoginPage({ onLoggedIn }) {
  const [view, setView] = useState('landing'); // landing | login | how | faq
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
              log.error('Sign-in failed:', err.message);
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
        log.error('Google sign-in failed to initialize:', err.message);
        if (!cancelled) setError(err.message);
      });

    return () => { cancelled = true; };
  }, [view, onLoggedIn]);

  if (view !== 'login') {
    return (
      <div className="landing">
        <LandingHeader view={view} onNavigate={setView} />
        <main className="landing-main">
          {view === 'landing' && (
            <div className="landing-hero">
              <h1 className="login-brand">Solveki</h1>
              <p className="login-subtitle">
                Master math for grades 1&ndash;12 and AP with spaced repetition.
              </p>
              <button className="login-cta" onClick={() => setView('login')}>
                Log in / Register
              </button>
            </div>
          )}
          {view === 'how' && <HowItWorks />}
          {view === 'faq' && <Faq />}
        </main>
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
