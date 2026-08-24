import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithClient } from './test-utils.jsx';

vi.mock('./auth.js', () => ({ apiFetch: vi.fn(), localDay: vi.fn(() => '2026-08-23') }));

import { apiFetch } from './auth.js';
import Diagnostic from './Diagnostic.jsx';
import { readDiagnostic, saveDiagnosticProgress } from './diagnosticStore.js';

const USER_ID = 1;

function jsonResponse(payload, { ok = true, status = 200 } = {}) {
  return { ok, status, json: async () => payload };
}

const CONFIG = {
  courses: [{ id: 1, course_name: 'Grade 8', grade_level: 8 }],
  units_by_course: {
    1: [
      { key: 'g8-u1', name: 'Real Numbers, Exponents & Scientific Notation' },
      { key: 'g8-u2', name: 'Linear Equations & Systems' },
    ],
  },
};

const START = { problems: [{ topic_id: 10, problem: '$1+1=$', solution: '2' }] };
const SUBMIT = { selected_count: 6, by_course: { 'Grade 8': 4, 'Grade 7': 2 } };

beforeEach(() => {
  apiFetch.mockReset();
  localStorage.clear();
});

function mockHappyPath() {
  apiFetch.mockImplementation((url = '') => {
    if (url === '/diagnostic/config/') return Promise.resolve(jsonResponse(CONFIG));
    if (url === '/diagnostic/start/') return Promise.resolve(jsonResponse(START));
    if (url.startsWith('/diagnostic/submit/')) return Promise.resolve(jsonResponse(SUBMIT));
    return Promise.resolve(jsonResponse({}));
  });
}

// Drive the two profile steps (course, unit) and start the calibration problem.
async function reachCalibration(user) {
  await screen.findByText(/What math course are you currently taking/);
  await user.selectOptions(screen.getByRole('combobox'), '1');
  await user.click(screen.getByRole('button', { name: 'Next' }));
  await screen.findByText('Which unit are you currently learning in this course?');
  await user.selectOptions(screen.getByRole('combobox'), 'g8-u2');
  await user.click(screen.getByRole('button', { name: 'Start problems' }));
  await screen.findByLabelText('Your answer');
}

function submitBody() {
  const call = apiFetch.mock.calls.find(([u]) => u.startsWith('/diagnostic/submit/'));
  return JSON.parse(call[1].body);
}

describe('Diagnostic', () => {
  it('walks course -> unit -> calibration -> results and marks the run completed', async () => {
    mockHappyPath();
    const onNavigate = vi.fn();
    const user = userEvent.setup();
    renderWithClient(<Diagnostic onNavigate={onNavigate} userId={USER_ID} />);

    await reachCalibration(user);
    await user.type(screen.getByLabelText('Your answer'), '2');
    await user.click(screen.getByRole('button', { name: 'Submit' }));

    await screen.findByText("You're all set!");
    expect(screen.getByText(/We selected/)).toHaveTextContent('We selected 6 topics');
    expect(screen.getByText('Grade 8: 4 topics')).toBeInTheDocument();

    expect(submitBody()).toMatchObject({
      current_course_id: 1,
      current_unit_key: 'g8-u2',
      results: [{ topic_id: 10, outcome: 'correct_first' }],
    });
    // Completing the run flips the stored status so the entry button offers "Retake".
    expect(readDiagnostic(USER_ID)?.status).toBe('completed');

    await user.click(screen.getByRole('button', { name: 'Start practicing' }));
    expect(onNavigate).toHaveBeenCalledWith('math');
  });

  it('starts the calibration problems for the chosen course + unit', async () => {
    mockHappyPath();
    const user = userEvent.setup();
    renderWithClient(<Diagnostic onNavigate={vi.fn()} userId={USER_ID} />);

    await reachCalibration(user);
    const startCall = apiFetch.mock.calls.find(([u]) => u === '/diagnostic/start/');
    expect(JSON.parse(startCall[1].body)).toEqual({
      current_course_id: 1,
      current_unit_key: 'g8-u2',
    });
  });

  it('exits via the X, leaving the run resumable', async () => {
    mockHappyPath();
    const onNavigate = vi.fn();
    const user = userEvent.setup();
    renderWithClient(<Diagnostic onNavigate={onNavigate} userId={USER_ID} />);

    await screen.findByText(/What math course are you currently taking/);
    await user.selectOptions(screen.getByRole('combobox'), '1');
    await user.click(screen.getByRole('button', { name: 'Next' }));
    await screen.findByText('Which unit are you currently learning in this course?');

    await user.click(screen.getByRole('button', { name: 'Exit diagnostic' }));
    expect(onNavigate).toHaveBeenCalledWith('courses');
    const saved = readDiagnostic(USER_ID);
    expect(saved?.status).toBe('in_progress');
    expect(saved.snapshot.profileStep).toBe(1); // stopped on the unit step
  });

  it('resumes an in-progress calibration from saved state', async () => {
    mockHappyPath();
    saveDiagnosticProgress(USER_ID, {
      phase: 'calibrate',
      profileStep: 1,
      currentCourseId: '1',
      currentUnitKey: 'g8-u2',
      problems: START.problems,
      problemIndex: 0,
      results: [],
    });
    renderWithClient(<Diagnostic onNavigate={vi.fn()} userId={USER_ID} />);

    // Lands straight on the calibration problem — no profile questions replayed,
    // and no /diagnostic/start/ refetch needed.
    await screen.findByLabelText('Your answer');
    expect(screen.queryByText(/What math course are you currently taking/)).not.toBeInTheDocument();
    expect(apiFetch.mock.calls.some(([u]) => u === '/diagnostic/start/')).toBe(false);
  });

  it('advances the progress bar only when moving to the next question', async () => {
    mockHappyPath();
    const user = userEvent.setup();
    renderWithClient(<Diagnostic onNavigate={vi.fn()} userId={USER_ID} />);

    await screen.findByText(/What math course are you currently taking/);
    const bar = screen.getByRole('progressbar');
    // The diagnostic is a fixed five questions; nothing is behind us yet.
    expect(bar).toHaveAttribute('aria-valuemax', '5');
    expect(bar).toHaveAttribute('aria-valuenow', '0');

    await user.selectOptions(screen.getByRole('combobox'), '1');
    await user.click(screen.getByRole('button', { name: 'Next' }));
    await screen.findByText('Which unit are you currently learning in this course?');
    // Moved onto the unit question: one step complete, total unchanged.
    const advanced = screen.getByRole('progressbar');
    expect(advanced).toHaveAttribute('aria-valuemax', '5');
    expect(advanced).toHaveAttribute('aria-valuenow', '1');
  });

  it('surfaces a config load failure with a way back', async () => {
    apiFetch.mockResolvedValue(jsonResponse({}, { ok: false, status: 500 }));
    const onNavigate = vi.fn();
    const user = userEvent.setup();
    renderWithClient(<Diagnostic onNavigate={onNavigate} userId={USER_ID} />);

    await screen.findByText(/Couldn't load the diagnostic/);
    await user.click(screen.getByRole('button', { name: 'Back to courses' }));
    expect(onNavigate).toHaveBeenCalledWith('courses');
  });
});
