import { useState, useEffect, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import DiagnosticProgress from './DiagnosticProgress.jsx';
import { apiFetch, localDay } from './auth.js';
import { createLogger } from './logger.js';
import {
  readDiagnostic,
  saveDiagnosticProgress,
  markDiagnosticCompleted,
} from './diagnosticStore.js';
import './Diagnostic.css';

const log = createLogger('diagnostic');

// Render '$...$' segments with KaTeX, plain text otherwise — mirrors the helper
// in MathProblem.jsx so calibration problems look identical to practice cards.
function InlineMath({ math }) {
  const html = katex.renderToString(math, { throwOnError: false });
  return <span dangerouslySetInnerHTML={{ __html: html }} />;
}
function renderMixedLatex(str) {
  if (!str) return null;
  return str.split('$').map((segment, i) =>
    i % 2 === 1 ? <InlineMath key={i} math={segment} /> : segment
  );
}

async function fetchDiagnosticConfig() {
  const res = await apiFetch('/diagnostic/config/');
  if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
  return res.json();
}

const PROFILE_STEPS = 2;          // current course, current unit
const CALIBRATION_PROBLEMS = 3;   // must match NUM_CALIBRATION_PROBLEMS on the backend
const TOTAL_STEPS = PROFILE_STEPS + CALIBRATION_PROBLEMS; // the diagnostic is 5 questions

// One calibration problem: two attempts, then reveal the answer. Reports the
// outcome ('correct_first' | 'correct_second' | 'incorrect') via onResolve, the
// same vocabulary the deck uses for SM-2 grading. Reuses the practice card's
// exact/float answer comparison (see MathProblemResponse.jsx). Keyed by the
// problem in the parent, so it remounts (resetting attempts) for each question.
function CalibrationCard({ problem, solution, onResolve }) {
  const MAX_ATTEMPTS = 2;
  const [attempt, setAttempt] = useState(1);
  const [response, setResponse] = useState('');
  const [wrong, setWrong] = useState(false);   // brief "Incorrect" flash
  const [revealed, setRevealed] = useState(false);
  const inputRef = useRef(null);

  useEffect(() => { inputRef.current?.focus(); }, []);

  const submit = () => {
    if (response.trim() === '') return;
    const numR = parseFloat(response);
    const numS = parseFloat(solution);
    const correct = response === solution ||
      (!isNaN(numR) && !isNaN(numS) && numR === numS);
    if (correct) {
      onResolve(attempt === 1 ? 'correct_first' : 'correct_second');
    } else if (attempt < MAX_ATTEMPTS) {
      setAttempt(attempt + 1);
      setResponse('');
      setWrong(true);
      setTimeout(() => setWrong(false), 1200);
    } else {
      setRevealed(true);
    }
  };

  const onKey = (e) => { if (e.key === 'Enter') submit(); };

  if (revealed) {
    return (
      <div className="diagnostic-card">
        <p className="diagnostic-reveal-answer">The answer was {solution}.</p>
        <div className="diagnostic-reveal-actions">
          <button className="diagnostic-btn diagnostic-btn-primary" onClick={() => onResolve('incorrect')}>
            Continue
          </button>
          <button className="diagnostic-btn diagnostic-btn-ghost" onClick={() => onResolve('correct_second')}>
            I actually got it right
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="diagnostic-card">
      <span className="diagnostic-attempt">Attempt {attempt} of {MAX_ATTEMPTS}</span>
      <div className="math-problem-display diagnostic-problem">{renderMixedLatex(problem)}</div>
      <div style={{ width: '100%', display: 'flex', gap: '8px' }}>
        <input
          ref={inputRef}
          className={`math-problem-input${wrong ? ' incorrect' : ''}`}
          value={response}
          onChange={(e) => setResponse(e.target.value)}
          onKeyPress={onKey}
          aria-label="Your answer"
        />
        <button
          className={`math-problem-submit${wrong ? ' math-problem-submit-incorrect' : ''}`}
          onClick={submit}
          disabled={response.trim() === ''}
        >
          {wrong ? 'Try again' : 'Submit'}
        </button>
      </div>
    </div>
  );
}

function Diagnostic({ onNavigate, userId }) {
  const queryClient = useQueryClient();
  const { data: config, isPending, error: configError } = useQuery({
    queryKey: ['diagnostic-config'],
    queryFn: fetchDiagnosticConfig,
  });

  // A half-finished run left in localStorage (user hit the X, closed the tab,
  // etc.) is resumed exactly where it stopped. Only the stable phases (profile /
  // calibrate) are ever persisted, so there's no transient state to restore.
  const resume = (() => {
    const saved = readDiagnostic(userId);
    return saved?.status === 'in_progress' ? saved.snapshot : null;
  })();

  // profile | loading | calibrate | submitting | done | submit_error
  const [phase, setPhase] = useState(resume?.phase ?? 'profile');
  const [profileStep, setProfileStep] = useState(resume?.profileStep ?? 0);
  const [currentCourseId, setCurrentCourseId] = useState(resume?.currentCourseId ?? '');
  const [currentUnitKey, setCurrentUnitKey] = useState(resume?.currentUnitKey ?? '');
  const [problems, setProblems] = useState(resume?.problems ?? []);
  const [problemIndex, setProblemIndex] = useState(resume?.problemIndex ?? 0);
  const [results, setResults] = useState(resume?.results ?? []); // {topic_id, outcome}
  const [summary, setSummary] = useState(null);
  const [runError, setRunError] = useState(null);

  // Persist resumable progress on every change. Opening the diagnostic at all
  // marks it "in progress", so the Courses button becomes "Resume Diagnostic"
  // even if the user backs out before answering anything.
  useEffect(() => {
    if (phase === 'profile' || phase === 'calibrate') {
      saveDiagnosticProgress(userId, {
        phase, profileStep, currentCourseId, currentUnitKey,
        problems, problemIndex, results,
      });
    }
  }, [phase, profileStep, currentCourseId, currentUnitKey,
      problems, problemIndex, results, userId]);

  // Units for the chosen course (the "which unit" dropdown). Keyed by course id
  // in the config; the select value is a string, matching the JSON object keys.
  const unitsForCurrentCourse = config?.units_by_course?.[currentCourseId] ?? [];

  // The progress bar only moves when the student advances to the next question:
  // it reflects how many of the five questions are behind them.
  let completedSteps;
  if (phase === 'profile') completedSteps = profileStep;
  else if (phase === 'calibrate' || phase === 'loading') completedSteps = PROFILE_STEPS + problemIndex;
  else completedSteps = TOTAL_STEPS; // submitting / done

  const submitDiagnostic = async (finalResults) => {
    setPhase('submitting');
    setRunError(null);
    try {
      const res = await apiFetch(`/diagnostic/submit/?today=${localDay()}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_course_id: currentCourseId ? Number(currentCourseId) : null,
          current_unit_key: currentUnitKey || null,
          results: finalResults.map((r) => ({ topic_id: r.topic_id, outcome: r.outcome })),
        }),
      });
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      const data = await res.json();
      setSummary(data);
      // Everything that shows selections / schedule must refresh.
      queryClient.invalidateQueries({ queryKey: ['courses'] });
      queryClient.invalidateQueries({ queryKey: ['all-topics'] });
      queryClient.invalidateQueries({ queryKey: ['topics'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['deck'] });
      log.info(`Diagnostic selected ${data.selected_count} topics`);
      markDiagnosticCompleted(userId); // Courses button now offers "Retake"
      setPhase('done');
    } catch (err) {
      log.error('Failed to submit diagnostic:', err.message);
      setRunError(err.message);
      setPhase('submit_error');
    }
  };

  const beginCalibration = async () => {
    setPhase('loading');
    setRunError(null);
    try {
      const res = await apiFetch('/diagnostic/start/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_course_id: currentCourseId ? Number(currentCourseId) : null,
          current_unit_key: currentUnitKey || null,
        }),
      });
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      const data = await res.json();
      if (!data.problems || data.problems.length === 0) {
        // Nothing to calibrate (rare) — go straight to selection on self-report.
        await submitDiagnostic([]);
        return;
      }
      setProblems(data.problems);
      setProblemIndex(0);
      setResults([]);
      setPhase('calibrate');
    } catch (err) {
      log.error('Failed to start diagnostic:', err.message);
      setRunError(err.message);
      setPhase('profile');
    }
  };

  const handleResolve = (outcome) => {
    const current = problems[problemIndex];
    const next = [...results, { topic_id: current.topic_id, outcome }];
    setResults(next);
    if (problemIndex + 1 < problems.length) {
      setProblemIndex(problemIndex + 1);
    } else {
      submitDiagnostic(next);
    }
  };

  // Changing the current course invalidates the unit answer (units are per course).
  const onCourseChange = (id) => {
    setCurrentCourseId(id);
    setCurrentUnitKey('');
  };

  if (isPending) return <div className="diagnostic" />;
  if (configError) {
    return (
      <div className="diagnostic">
        <p className="diagnostic-error">Couldn't load the diagnostic: {configError.message}</p>
        <button className="diagnostic-btn diagnostic-btn-ghost" onClick={() => onNavigate('courses')}>
          Back to courses
        </button>
      </div>
    );
  }

  // A course with authored units requires a unit answer before starting; a course
  // with none (rare) starts on the current course as a whole.
  const unitRequired = unitsForCurrentCourse.length > 0;

  return (
    <div className="diagnostic">
      {phase !== 'done' && (
        <button
          className="diagnostic-exit"
          onClick={() => onNavigate('courses')}
          aria-label="Exit diagnostic"
          title="Exit — you can resume later"
        >
          ×
        </button>
      )}
      <div className="diagnostic-intro">
        <h1 className="diagnostic-title">Quick diagnostic</h1>
        <p className="diagnostic-subtitle">
          Answer two quick questions and solve three problems. We'll pick the
          right topics for you to review — no need to hunt through every course.
        </p>
      </div>

      {phase !== 'done' && <DiagnosticProgress completed={completedSteps} total={TOTAL_STEPS} />}
      {runError && phase === 'profile' && <p className="diagnostic-error">{runError}</p>}

      {/* ---- Profile step 0: current course ---- */}
      {phase === 'profile' && profileStep === 0 && (
        <div className="diagnostic-card">
          <label className="diagnostic-question" htmlFor="diagnostic-course">
            What math course are you currently taking (or most recently took)?
          </label>
          <select
            id="diagnostic-course"
            className="diagnostic-select"
            value={currentCourseId}
            onChange={(e) => onCourseChange(e.target.value)}
          >
            <option value="" disabled>Choose a course…</option>
            {config.courses.map((c) => (
              <option key={c.id} value={c.id}>{c.course_name}</option>
            ))}
          </select>
          <div className="diagnostic-nav">
            <button className="diagnostic-btn diagnostic-btn-ghost" onClick={() => onNavigate('courses')}>
              Cancel
            </button>
            <button
              className="diagnostic-btn diagnostic-btn-primary"
              onClick={() => setProfileStep(1)}
              disabled={!currentCourseId}
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* ---- Profile step 1: current unit ---- */}
      {phase === 'profile' && profileStep === 1 && (
        <div className="diagnostic-card">
          <label className="diagnostic-question" htmlFor="diagnostic-unit">
            Which unit are you currently learning in this course?
          </label>
          {unitRequired ? (
            <select
              id="diagnostic-unit"
              className="diagnostic-select"
              value={currentUnitKey}
              onChange={(e) => setCurrentUnitKey(e.target.value)}
            >
              <option value="" disabled>Choose a unit…</option>
              {unitsForCurrentCourse.map((u) => (
                <option key={u.key} value={u.key}>{u.name}</option>
              ))}
            </select>
          ) : (
            <p className="diagnostic-note">
              We'll review this whole course with you.
            </p>
          )}
          <div className="diagnostic-nav">
            <button className="diagnostic-btn diagnostic-btn-ghost" onClick={() => setProfileStep(0)}>
              Back
            </button>
            <button
              className="diagnostic-btn diagnostic-btn-primary"
              onClick={beginCalibration}
              disabled={unitRequired && !currentUnitKey}
            >
              Start problems
            </button>
          </div>
        </div>
      )}

      {/* ---- Loading / submitting ---- */}
      {(phase === 'loading' || phase === 'submitting') && (
        <div className="diagnostic-card diagnostic-card-centered">
          <span className="diagnostic-question">
            {phase === 'loading' ? 'Preparing your problems…' : 'Picking your topics…'}
          </span>
        </div>
      )}

      {/* ---- Calibration problems ---- */}
      {phase === 'calibrate' && problems[problemIndex] && (
        <CalibrationCard
          key={problemIndex}
          problem={problems[problemIndex].problem}
          solution={problems[problemIndex].solution}
          onResolve={handleResolve}
        />
      )}

      {/* ---- Submit failed ---- */}
      {phase === 'submit_error' && (
        <div className="diagnostic-card diagnostic-card-centered">
          <p className="diagnostic-error">Something went wrong saving your results: {runError}</p>
          <button className="diagnostic-btn diagnostic-btn-primary" onClick={() => submitDiagnostic(results)}>
            Try again
          </button>
        </div>
      )}

      {/* ---- Done ---- */}
      {phase === 'done' && summary && (
        <div className="diagnostic-card diagnostic-card-centered">
          <h2 className="diagnostic-done-title">You're all set!</h2>
          <p className="diagnostic-done-text">
            We selected <strong>{summary.selected_count}</strong> topic{summary.selected_count === 1 ? '' : 's'} for you to review.
          </p>
          {summary.by_course && Object.keys(summary.by_course).length > 0 && (
            <ul className="diagnostic-summary-list">
              {Object.entries(summary.by_course)
                .filter(([, count]) => count > 0)
                .map(([name, count]) => (
                  <li key={name}>{name}: {count} topic{count === 1 ? '' : 's'}</li>
                ))}
            </ul>
          )}
          <div className="diagnostic-nav diagnostic-nav-center">
            <button className="diagnostic-btn diagnostic-btn-ghost" onClick={() => onNavigate('courses')}>
              Review selections
            </button>
            <button className="diagnostic-btn diagnostic-btn-primary" onClick={() => onNavigate('math')}>
              Start practicing
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default Diagnostic;
