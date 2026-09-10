import { useState } from 'react';
import { setRole } from './auth.js';
import { createLogger } from './logger.js';
import './RolePicker.css';

const log = createLogger('role-picker');

// Shown once, right after a brand-new user signs in, to choose whether they're
// a student or a teacher. The choice is locked server-side after the first set
// (see the /settings/role/ endpoint), so this is a one-time onboarding step.
//
// Students are asked for their first and last name — that's the name their
// teachers see in class rosters and student detail. Teachers keep the name
// their Google account already provides, so they skip the name step.
function RolePicker({ onChosen }) {
  const [step, setStep] = useState('role'); // 'role' | 'student-name'
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  async function finish(role, names) {
    setError(null);
    setSubmitting(true);
    try {
      const data = await setRole(role, names || {});
      onChosen(role, data.name);
    } catch (err) {
      log.error('Failed to set role:', err.message);
      setError(err.message);
      setSubmitting(false);
    }
  }

  function submitStudentName(e) {
    e.preventDefault();
    finish('student', { firstName: firstName.trim(), lastName: lastName.trim() });
  }

  if (step === 'student-name') {
    return (
      <div className="role-picker">
        <h1 className="role-picker-brand">Welcome to Solveki</h1>
        <p className="role-picker-subtitle">What's your name?</p>
        <form className="role-picker-name-form" onSubmit={submitStudentName}>
          <label className="role-picker-field">
            <span>First name</span>
            <input
              type="text"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              autoFocus
              autoComplete="given-name"
            />
          </label>
          <label className="role-picker-field">
            <span>Last name</span>
            <input
              type="text"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              autoComplete="family-name"
            />
          </label>
          <div className="role-picker-name-actions">
            <button
              type="button"
              className="role-picker-back"
              disabled={submitting}
              onClick={() => { setStep('role'); setError(null); }}
            >
              ← Back
            </button>
            <button
              type="submit"
              className="role-picker-continue"
              disabled={submitting || !firstName.trim() || !lastName.trim()}
            >
              {submitting ? 'Saving…' : 'Continue'}
            </button>
          </div>
        </form>
        {error && <p className="role-picker-error">{error}</p>}
      </div>
    );
  }

  return (
    <div className="role-picker">
      <h1 className="role-picker-brand">Welcome to Solveki</h1>
      <p className="role-picker-subtitle">How will you be using Solveki?</p>
      <div className="role-picker-options">
        <button
          className="role-picker-card"
          disabled={submitting}
          onClick={() => { setError(null); setStep('student-name'); }}
        >
          <span className="role-picker-card-title">I'm a student</span>
          <span className="role-picker-card-desc">
            Practice topics with spaced repetition and complete assignments from
            your teacher.
          </span>
        </button>
        <button
          className="role-picker-card"
          disabled={submitting}
          onClick={() => finish('teacher')}
        >
          <span className="role-picker-card-title">I'm a teacher</span>
          <span className="role-picker-card-desc">
            Create classes and assignments, and track your students' progress.
          </span>
        </button>
      </div>
      {error && <p className="role-picker-error">{error}</p>}
    </div>
  );
}

export default RolePicker;
