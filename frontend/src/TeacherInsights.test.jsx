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

    fireEvent.click(await screen.findByRole('tab', { name: /Topics/ }));
    const struggled = screen.getByText('Struggled with most').parentElement;
    expect(within(struggled).getByText('Decimals')).toBeInTheDocument();
    expect(within(struggled).getByText(/25% right first try · 8 answers · 3 students missed it/)).toBeInTheDocument();

    // One bar per band for the picked topic, the first by default.
    const bar = (name) => screen.getByRole('img', { name });
    expect(bar('Fractions, Familiar: 2 students')).toBeInTheDocument();
    expect(bar('Fractions, New: 1 student')).toBeInTheDocument();

    // Hovering a bar shows its share of the topic's students.
    fireEvent.mouseEnter(bar('Fractions, Familiar: 2 students').closest('.tbc-col'));
    const card = screen.getByRole('tooltip');
    expect(within(card).getByText('2 of 4 students')).toBeInTheDocument();
    expect(within(card).getByText('50%')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Topic'), { target: { value: '2' } });
    expect(bar('Decimals, New: 4 students')).toBeInTheDocument();
    expect(bar('Decimals, Familiar: 0 students')).toBeInTheDocument();
  });

  it('draws each student’s familiarity timeline and shows the date on hover', async () => {
    apiFetch.mockResolvedValueOnce(json({
      assignment: { title: 'HW 1', deck_size: 10, classes: [] },
      topics: [], struggled: [], num_students: 1, num_completed: 0, band_totals: {},
      timeline_range: { start: '2026-10-01', end: '2026-10-10' },
      students: [{
        student_id: 1, name: 'Ada', class_id: 1, due_at: null, cards_answered: 0,
        completion_pct: 0, max_reached: false, late: false, overdue: false, status: 'in_progress',
        proficiency: BANDS_MIXED,
        timeline: [
          { band: 'new', start: '2026-10-03', end: '2026-10-05' },
          { band: 'learning', start: '2026-10-06', end: '2026-10-10' },
        ],
      }],
    }));
    renderWithClient(<AssignmentDetail assignmentId={7} onOpenStudent={() => {}} />);

    const row = (await screen.findByRole('cell', { name: 'Ada' })).closest('tr');
    const bar = within(row).getByRole('img');
    expect(bar).toHaveAccessibleName('New Oct 3–Oct 5, Learning Oct 6–Oct 10');
    expect(apiFetch).toHaveBeenCalledWith('/assignments/7/results/?today=2026-10-24');

    // 10 days across 100px: x=75 is the 8th day, Oct 8.
    const hit = bar.parentElement;
    hit.getBoundingClientRect = () => ({ left: 0, width: 100, top: 0, height: 10 });
    fireEvent.mouseMove(hit, { clientX: 75 });
    const card = within(row).getByRole('tooltip');
    expect(within(card).getByText('Oct 8')).toBeInTheDocument();
    expect(within(card).getByText('Learning')).toBeInTheDocument();
    expect(within(card).getByText('since Oct 6')).toBeInTheDocument();

    // Before the assignment reached the student.
    fireEvent.mouseMove(hit, { clientX: 5 });
    expect(within(row).getByText('Not assigned yet')).toBeInTheDocument();
    fireEvent.mouseLeave(hit);
    expect(within(row).queryByRole('tooltip')).toBeNull();
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

    expect(await screen.findByText(/At least 10 cards \(up to 15 for students who struggle\)/)).toBeInTheDocument();
    expect(screen.getByText(/10–15 cards · no late work/)).toBeInTheDocument();
    const row = (name) => screen.getByRole('cell', { name }).closest('tr');
    expect(within(row('Ada')).getByText('40%')).toBeInTheDocument();
    expect(within(row('Ben')).getByText('Needs help')).toBeInTheDocument();
    expect(within(row('Cy')).getByText('Late')).toBeInTheDocument();
    expect(within(row('Cy')).queryByText('Needs help')).not.toBeInTheDocument();
  });

  it('says so when there are no misses yet', async () => {
    apiFetch.mockResolvedValueOnce(json({
      assignment: { title: 'HW 1', deck_size: 10, classes: [] },
      topics: [], struggled: [], num_students: 0, num_completed: 0,
      band_totals: {}, students: [],
    }));
    renderWithClient(<AssignmentDetail assignmentId={7} onOpenStudent={() => {}} />);
    fireEvent.click(await screen.findByRole('tab', { name: /Topics/ }));
    expect(screen.getByText('No misses on these topics yet.')).toBeInTheDocument();
  });

  it('counts students by status and filters the table from the counters', async () => {
    const student = (id, name, extra) => ({
      student_id: id, name, class_id: 1, due_at: null, cards_answered: 0, cards_needed: 10,
      completion_pct: 0, max_reached: false, late: false, overdue: false,
      status: 'in_progress', proficiency: BANDS_MIXED, timeline: [], ...extra,
    });
    apiFetch.mockResolvedValueOnce(json({
      assignment: { title: 'HW 1', deck_size: 10, max_cards: 15, allow_late: true, classes: [] },
      topics: [], struggled: [], students: [
        student(1, 'Ada', { status: 'not_started', overdue: true }),
        student(2, 'Ben', { cards_answered: 4, completion_pct: 40, accuracy: 75, topics_solid: 1 }),
        student(3, 'Cy', { status: 'done', completion_pct: 100, cards_answered: 15, max_reached: true }),
      ],
    }));
    const onOpenStudent = vi.fn();
    renderWithClient(<AssignmentDetail assignmentId={7} onOpenStudent={onOpenStudent} />);

    const counters = await screen.findByRole('group', { name: 'Filter by status' });
    const counter = (label) => within(counters).getByRole('button', { name: new RegExp(label) });
    expect(counter('Assigned')).toHaveTextContent('3');
    expect(counter('Overdue')).toHaveTextContent('1');
    expect(counter('Needs help')).toHaveTextContent('1');

    // Needs attention first: overdue, then needs help, then the rest.
    const names = () => screen.getAllByRole('row').slice(1).map((r) => within(r).getAllByRole('cell')[0].textContent);
    expect(names()).toEqual(['Ada', 'Cy', 'Ben']);
    expect(screen.getByText('4 of 10 cards')).toBeInTheDocument();
    expect(screen.getByText('75%')).toBeInTheDocument();

    fireEvent.click(counter('In progress'));
    expect(names()).toEqual(['Ben']);
    fireEvent.click(counter('In progress'));
    expect(names()).toHaveLength(3);

    fireEvent.click(screen.getByRole('button', { name: 'Ben' }));
    expect(onOpenStudent).toHaveBeenCalledWith(2, 1);
  });
});

describe('ClassDetail', () => {
  const CLASS = { id: 1, name: 'Period 1', join_code: 'ABC234', student_count: 1 };
  const PROGRESS = {
    assignment_id: 7,
    assignments: [{ id: 7, title: 'Unit 4' }],
    topics: [{ topic_id: 1, topic_name: 'Slope' }, { topic_id: 2, topic_name: 'Systems' }],
    students: [
      { id: 3, name: 'Ada', last_active: '2026-10-24', cells: { 1: { band: 'familiar', missed_recent: false }, 2: { band: 'new', missed_recent: true } } },
      { id: 4, name: 'Ben', last_active: null, cells: { 1: null, 2: null } },
    ],
    topic_summary: { 1: 50, 2: 0 },
  };

  function route(extra = {}) {
    apiFetch.mockImplementation(async (url, opts) => {
      if (opts?.method === 'PATCH') return json({ ...CLASS, ...JSON.parse(opts.body) });
      if (url.startsWith('/classes/1/students/')) {
        return json({ students: [{
          id: 3, name: 'Ada', email: 'a@x.org', joined_at: '2026-10-01T00:00:00Z', proficiency: BANDS_MIXED,
          cards_7d: 12, accuracy_7d: 80, last_active: '2026-10-23', overdue_count: 2,
        }] });
      }
      if (url.startsWith('/classes/1/progress/')) return json(PROGRESS);
      if (url.startsWith('/assignments/')) return json({ assignments: extra.assignments || [] });
      return json(CLASS);
    });
  }

  it('lists students with their familiarity, week and overdue work', async () => {
    route();
    renderWithClient(<ClassDetail classId={1} onOpenStudent={() => {}} />);

    const row = (await screen.findByRole('button', { name: 'Ada' })).closest('tr');
    expect(within(row).getByRole('img'))
      .toHaveAccessibleName('New: 1, Learning: 0, Familiar: 2, Proficient: 1');
    expect(within(row).getByText('12')).toBeInTheDocument();
    expect(within(row).getByText('80%')).toBeInTheDocument();
    expect(within(row).getByText('Yesterday')).toBeInTheDocument();
    expect(within(row).getByText('2 overdue')).toBeInTheDocument();
    expect(apiFetch).toHaveBeenCalledWith('/classes/1/students/?today=2026-10-24');
  });

  it('shows the students x topics grid, and hides names for projecting', async () => {
    route();
    renderWithClient(<ClassDetail classId={1} onOpenStudent={() => {}} />);
    fireEvent.click(await screen.findByRole('tab', { name: 'Progress' }));

    expect(await screen.findByLabelText('Ada, Slope: Familiar')).toHaveTextContent('F');
    expect(screen.getByLabelText('Ada, Systems: New, missed lately')).toHaveClass('miss');
    expect(screen.getByLabelText('Ben, Slope: Not started')).toHaveTextContent('–');
    expect(screen.getByText('50%')).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText('Hide names (for projecting)'));
    expect(screen.queryByRole('button', { name: 'Ada' })).toBeNull();
    expect(screen.getByRole('button', { name: 'Student 1' })).toBeInTheDocument();
  });

  it('renames and archives the class from settings, archiving only after confirm', async () => {
    route();
    const onBack = vi.fn();
    renderWithClient(<ClassDetail classId={1} onBack={onBack} onOpenStudent={() => {}} />);
    fireEvent.click(await screen.findByRole('tab', { name: 'Settings' }));

    fireEvent.change(await screen.findByLabelText('Class name'), { target: { value: 'Period 2' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save name' }));
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith('/classes/1/', expect.objectContaining({
      method: 'PATCH', body: JSON.stringify({ name: 'Period 2' }),
    })));

    fireEvent.click(screen.getByRole('button', { name: 'Archive class' }));
    const dialog = screen.getByRole('dialog');
    fireEvent.click(within(dialog).getByRole('button', { name: 'Archive class' }));
    await waitFor(() => expect(onBack).toHaveBeenCalled());
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
    expect(screen.getByText(/no practice in the last 7 days/)).toBeInTheDocument();
  });

  it('shows the most recent assignments first, the rest behind "View more"', async () => {
    const assignment = (id, day, extra = {}) => ({
      assignment_id: id, title: `Set ${id}`, class_name: 'Period 1',
      status: 'not_started', completion_pct: 0, max_reached: false, overdue: false,
      assigned_at: `2026-10-${day}T12:00:00Z`, due_at: null, ...extra,
    });
    apiFetch.mockResolvedValueOnce(json({
      student: { id: 3, name: 'Ada', email: 'a@x.org' },
      topics: [], upcoming: [],
      assignments: [
        assignment(1, 10, { overdue: true }), assignment(2, 20), assignment(3, 12),
        assignment(4, 15), assignment(5, 18),
      ],
      activity: { days, days_practiced: 3, streak: 3, week: { cards_answered: 5, seconds: 60, accuracy: 80 } },
      struggled: [],
    }));
    renderWithClient(<StudentDetail studentId={3} />);

    await screen.findByText('Set 2');
    const titles = () => screen.getAllByText(/^Set \d$/).map((el) => el.textContent);
    expect(titles()).toEqual(['Set 2', 'Set 5', 'Set 4']);
    expect(screen.getByText(/1 overdue assignment/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'View more (2)' }));
    expect(titles()).toEqual(['Set 2', 'Set 5', 'Set 4', 'Set 3', 'Set 1']);
  });

  it('opens an assignment from its row', async () => {
    apiFetch.mockResolvedValueOnce(json({
      student: { id: 3, name: 'Ada', email: 'a@x.org' },
      topics: [], upcoming: [],
      assignments: [{
        assignment_id: 9, title: 'Fractions', class_name: 'Period 1', status: 'done',
        assigned_at: '2026-10-10T12:00:00Z', due_at: null,
      }],
      activity: null, struggled: [],
    }));
    const onOpenAssignment = vi.fn();
    renderWithClient(<StudentDetail studentId={3} onOpenAssignment={onOpenAssignment} />);

    fireEvent.click(await screen.findByText('Fractions'));
    expect(onOpenAssignment).toHaveBeenCalledWith(9);
  });

  it('groups topics by proficiency without the pie chart', async () => {
    apiFetch.mockResolvedValueOnce(json({
      student: { id: 3, name: 'Ada', email: 'a@x.org' },
      topics: [
        { id: 1, topic_name: 'Ratios', interval: 1 },
        { id: 2, topic_name: 'Slope', interval: 30 },
      ],
      upcoming: [], assignments: [],
      activity: { days, days_practiced: 3, streak: 3, week: { cards_answered: 5, seconds: 60, accuracy: 80 } },
      struggled: [],
    }));
    renderWithClient(<StudentDetail studentId={3} />);

    expect(await screen.findByText('Topics by proficiency')).toBeInTheDocument();
    expect(screen.getByText('Ratios')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Proficient' })).toBeInTheDocument();
    expect(screen.queryByRole('img', { name: 'Topic proficiency mix' })).not.toBeInTheDocument();
  });

  it('previews a few topics per deck, the rest behind "Show more"', async () => {
    const topics = ['A', 'B', 'C', 'D', 'E'].map((name, i) => ({ id: i, topic_name: name, interval: 1 }));
    apiFetch.mockResolvedValueOnce(json({
      student: { id: 3, name: 'Ada', email: 'a@x.org' },
      topics, upcoming: [], assignments: [], activity: null, struggled: [],
    }));
    renderWithClient(<StudentDetail studentId={3} />);

    expect(await screen.findByText('D')).toBeInTheDocument();
    expect(screen.queryByText('E')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Show 1 more' }));
    expect(screen.getByText('E')).toBeInTheDocument();
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

  it('opens the card at once when a topic is clicked', async () => {
    route(FOCUS);
    renderWithClient(<TeacherOverview onOpenClass={() => {}} />);
    const fresh = await screen.findByRole('region', { name: 'Newly taught' });

    fireEvent.click(within(fresh).getByText('Fractions').closest('li'));
    const card = screen.getByRole('tooltip');
    expect(within(card).getByText('Average accuracy 67%')).toBeInTheDocument();
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
