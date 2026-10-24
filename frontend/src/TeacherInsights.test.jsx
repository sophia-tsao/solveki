import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, within } from '@testing-library/react';
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
