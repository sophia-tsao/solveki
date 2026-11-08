import { describe, it, expect, beforeEach, vi } from 'vitest';
import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import { renderWithClient } from './test-utils.jsx';

// Script the network layer; the trend chart has its own fetch and is irrelevant here.
vi.mock('./auth.js', () => ({
  apiFetch: vi.fn(),
  localDay: vi.fn(() => '2026-10-24'),
}));
vi.mock('./ProficiencyTrend.jsx', () => ({ default: () => null }));

import { apiFetch } from './auth.js';
import AssignmentDetail from './AssignmentDetail.jsx';
import ClassDetail from './ClassDetail.jsx';
import StudentDetail from './StudentDetail.jsx';
import TeacherOverview from './TeacherOverview.jsx';

function json(payload) {
  return { ok: true, status: 200, json: async () => payload };
}

const BANDS_MIXED = { new: 1, learning: 0, familiar: 2, proficient: 1 };

beforeEach(() => {
  apiFetch.mockReset();
});

describe('AssignmentDetail', () => {
  it('shows familiarity per topic and the topics students struggled with most', async () => {
    apiFetch.mockResolvedValueOnce(json({
      assignment: { title: 'HW 1', deck_size: 10, classes: [] },
      topics: [
        { topic_id: 1, topic_name: 'Fractions', proficiency: BANDS_MIXED },
        { topic_id: 2, topic_name: 'Decimals', proficiency: { new: 4, learning: 0, familiar: 0, proficient: 0 } },
      ],
      struggled: [
        { topic_id: 2, topic_name: 'Decimals', accuracy: 25, answers: 8, students: 3 },
      ],
      num_students: 4,
      num_completed: 1,
      band_totals: BANDS_MIXED,
      students: [],
    }));
    renderWithClient(<AssignmentDetail assignmentId={7} onOpenStudent={() => {}} />);

    const struggled = (await screen.findByText('Struggled with most')).parentElement;
    expect(within(struggled).getByText('Decimals')).toBeInTheDocument();
    expect(within(struggled).getByText(/25% right first try · 8 answers · 3 students missed it/)).toBeInTheDocument();

    const fractionsRow = screen.getByRole('cell', { name: 'Fractions' }).closest('tr');
    expect(within(fractionsRow).getByRole('img'))
      .toHaveAccessibleName('New: 1, Learning: 0, Familiar: 2, Proficient: 1');
  });

  it('shows each student’s completion with needs-help and late flags', async () => {
    const student = (id, name, extra) => ({
      student_id: id, name, class_id: 1, due_at: null, cards_answered: 0,
      completion_pct: 0, max_reached: false, late: false, overdue: false,
      status: 'in_progress', proficiency: BANDS_MIXED, ...extra,
    });
    apiFetch.mockResolvedValueOnce(json({
      assignment: { title: 'HW 1', deck_size: 10, max_cards: 15, allow_late: false, classes: [] },
      topics: [], struggled: [], num_students: 3, num_completed: 2,
      band_totals: BANDS_MIXED,
      students: [
        student(1, 'Ada', { completion_pct: 40 }),
        student(2, 'Ben', { status: 'done', completion_pct: 100, max_reached: true }),
        student(3, 'Cy', { status: 'done', completion_pct: 100, late: true }),
      ],
    }));
    renderWithClient(<AssignmentDetail assignmentId={7} onOpenStudent={() => {}} />);

    expect(await screen.findByText(/at least 10 cards \(up to 15 for students who struggle\)/)).toBeInTheDocument();
    expect(screen.getByText(/no late work/)).toBeInTheDocument();
    const row = (name) => screen.getByRole('cell', { name }).closest('tr');
    expect(within(row('Ada')).getByText('40%')).toBeInTheDocument();
    expect(within(row('Ben')).getByText(/needs help/)).toBeInTheDocument();
    expect(within(row('Cy')).getByText(/late/)).toBeInTheDocument();
    expect(within(row('Cy')).queryByText(/needs help/)).not.toBeInTheDocument();
  });

  it('says so when there are no misses yet', async () => {
    apiFetch.mockResolvedValueOnce(json({
      assignment: { title: 'HW 1', deck_size: 10, classes: [] },
      topics: [], struggled: [], num_students: 0, num_completed: 0,
      band_totals: {}, students: [],
    }));
    renderWithClient(<AssignmentDetail assignmentId={7} onOpenStudent={() => {}} />);
    expect(await screen.findByText('No misses on these topics yet.')).toBeInTheDocument();
  });
});

describe('ClassDetail', () => {
  it('gives each student a familiarity bar', async () => {
    apiFetch.mockImplementation(async (url) => (
      url.endsWith('/students/')
        ? json({ students: [{ id: 3, name: 'Ada', email: 'a@x.org', joined_at: '2026-10-01T00:00:00Z', proficiency: BANDS_MIXED }] })
        : json({ id: 1, name: 'Period 1', join_code: 'ABC234', student_count: 1 })
    ));
    renderWithClient(<ClassDetail classId={1} onOpenStudent={() => {}} />);

    const row = (await screen.findByRole('cell', { name: 'Ada' })).closest('tr');
    expect(within(row).getByRole('img'))
      .toHaveAccessibleName('New: 1, Learning: 0, Familiar: 2, Proficient: 1');
  });
});

describe('StudentDetail', () => {
  // 28 days ending 2026-10-24, the last three practiced.
  const days = Array.from({ length: 28 }, (_, i) => ({
    date: new Date(Date.UTC(2026, 8, 27 + i)).toISOString().slice(0, 10),
    status: i >= 25 ? 'completed' : 'none',
  }));

  it('shows practice consistency, this week, and struggled topics', async () => {
    apiFetch.mockResolvedValueOnce(json({
      student: { id: 3, name: 'Ada', email: 'a@x.org' },
      topics: [], upcoming: [], assignments: [],
      activity: {
        days, days_practiced: 3, streak: 3,
        week: { cards_answered: 42, seconds: 3900, accuracy: 81 },
      },
      struggled: [{ topic_id: 5, topic_name: 'Ratios', accuracy: 40, answers: 5, students: 1 }],
    }));
    renderWithClient(<StudentDetail studentId={3} />);

    expect(await screen.findByText('3 of last 28 days')).toBeInTheDocument();
    expect(screen.getByText('3-day streak')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('1h 5m')).toBeInTheDocument();
    expect(screen.getByText('81%')).toBeInTheDocument();
    expect(screen.getByText('Ratios')).toBeInTheDocument();
    // The local day is sent so "today" and the week follow the teacher's calendar.
    expect(apiFetch).toHaveBeenCalledWith('/teacher/students/3/?today=2026-10-24');
  });

  it('shows a dash for accuracy when nothing was answered this week', async () => {
    apiFetch.mockResolvedValueOnce(json({
      student: { id: 3, name: 'Ada', email: 'a@x.org' },
      topics: [], upcoming: [], assignments: [],
      activity: { days, days_practiced: 0, streak: 0, week: { cards_answered: 0, seconds: 0, accuracy: null } },
      struggled: [],
    }));
    renderWithClient(<StudentDetail studentId={3} />);

    expect(await screen.findByText('No current streak')).toBeInTheDocument();
    expect(screen.getByText('—')).toBeInTheDocument();
    expect(screen.getByText('0s')).toBeInTheDocument();
  });
});

describe('TeacherOverview', () => {
  const FOCUS = {
    newly_taught: [{
      topic_id: 1, topic_name: 'Fractions', first_assigned: '2026-10-20', accuracy: 67,
      proficiency: BANDS_MIXED,
    }],
    weak_spots: [{ topic_id: 3, topic_name: 'Ratios', accuracy: 20, missed_recent: 3 }],
    windows: { new_days: 14, missed_days: 14 },
  };

  function route(focus) {
    apiFetch.mockImplementation(async (url) => (
      url.startsWith('/teacher/overview/focus/')
        ? json(focus)
        : json({ classes: [{ id: 5, name: 'P1', student_count: 4 }], total_students: 4 })
    ));
  }

  // Rest the pointer on a topic row and wait out the hover delay.
  async function hover(region, name) {
    fireEvent.mouseEnter(within(region).getByText(name).closest('li'));
    return screen.findByRole('tooltip', {}, { timeout: 2000 });
  }

  it('shows each topic as a name over a bar', async () => {
    route(FOCUS);
    renderWithClient(<TeacherOverview onOpenClass={() => {}} />);

    const fresh = await screen.findByRole('region', { name: 'Newly taught' });
    expect(within(fresh).getByText('Fractions')).toBeInTheDocument();
    expect(within(fresh).getByRole('img'))
      .toHaveAccessibleName('New: 1, Learning: 0, Familiar: 2, Proficient: 1');

    const weak = screen.getByRole('region', { name: 'Weak spots' });
    expect(within(weak).getByRole('img')).toHaveAccessibleName('Average accuracy: 20%');
    expect(within(weak).getByText('Bars show average accuracy')).toBeInTheDocument();
    // No numbered lists, and no native hover text.
    expect(document.querySelector('.focus-col ol')).toBeNull();
    expect(document.querySelector('.focus-cols [title]')).toBeNull();
    expect(screen.queryByRole('tooltip')).toBeNull();
  });

  it('opens a newly taught card after a one-second hover', async () => {
    route(FOCUS);
    renderWithClient(<TeacherOverview onOpenClass={() => {}} />);
    const fresh = await screen.findByRole('region', { name: 'Newly taught' });

    fireEvent.mouseEnter(within(fresh).getByText('Fractions').closest('li'));
    // Not before the delay.
    await new Promise((r) => setTimeout(r, 500));
    expect(screen.queryByRole('tooltip')).toBeNull();

    const card = await screen.findByRole('tooltip', {}, { timeout: 2000 });
    expect(within(card).getByText(/^First assigned /)).toBeInTheDocument();
    expect(within(card).getByText('Average accuracy 67%')).toBeInTheDocument();
    // The percentages go in the topic's own bar; the card has no bar of its own.
    expect(within(card).queryByRole('img')).toBeNull();
    expect(within(fresh).getByRole('img'))
      .toHaveAccessibleName('New: 25%, Learning: 0%, Familiar: 50%, Proficient: 25%');
    expect(within(fresh).getByText('50%')).toBeInTheDocument();
  });

  it('cancels the card when the pointer leaves early', async () => {
    route(FOCUS);
    renderWithClient(<TeacherOverview onOpenClass={() => {}} />);
    const fresh = await screen.findByRole('region', { name: 'Newly taught' });

    const row = within(fresh).getByText('Fractions').closest('li');
    fireEvent.mouseEnter(row);
    fireEvent.mouseLeave(row);
    await new Promise((r) => setTimeout(r, 1200));
    expect(screen.queryByRole('tooltip')).toBeNull();
  });

  it('shows who missed a weak spot and its accuracy in the bar', async () => {
    route(FOCUS);
    renderWithClient(<TeacherOverview onOpenClass={() => {}} />);
    const weak = await screen.findByRole('region', { name: 'Weak spots' });

    const card = await hover(weak, 'Ratios');
    expect(within(card).getByText('3 students answered incorrectly in the past 2 weeks')).toBeInTheDocument();
    expect(within(card).queryByRole('img')).toBeNull();
    expect(within(weak).getByText('20%')).toBeInTheDocument();
  });

  it('shows empty states and scopes the columns by class', async () => {
    route({ ...FOCUS, newly_taught: [], weak_spots: [] });
    renderWithClient(<TeacherOverview onOpenClass={() => {}} />);

    expect(await screen.findByText('No assignments added new topics in the last 14 days.')).toBeInTheDocument();
    expect(screen.queryByRole('region', { name: 'About to be forgotten' })).toBeNull();
    expect(screen.getByText('No missed answers yet.')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Show'), { target: { value: '5' } });
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith(
      expect.stringMatching(/^\/teacher\/overview\/focus\/\?.*scope=class&class_id=5/),
    ));
  });
});
