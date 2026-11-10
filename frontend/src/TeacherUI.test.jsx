import { describe, it, expect, beforeEach, vi } from 'vitest';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { renderWithClient } from './test-utils.jsx';

vi.mock('./auth.js', () => ({
  apiFetch: vi.fn(),
  localDay: vi.fn(() => '2026-10-24'),
}));

import { apiFetch } from './auth.js';
import TeacherAssignments from './TeacherAssignments.jsx';
import { AssignmentStatusChips } from './ui/StatusChip.jsx';
import { useSortable } from './ui/useSortable.js';

function json(payload) {
  return { ok: true, status: 200, json: async () => payload };
}

beforeEach(() => {
  apiFetch.mockReset();
});

describe('AssignmentStatusChips', () => {
  it('labels every state in words, not color alone', () => {
    render(<AssignmentStatusChips row={{ status: 'done', late: true, max_reached: true }} />);
    expect(screen.getByText('Done')).toBeInTheDocument();
    expect(screen.getByText('Late')).toBeInTheDocument();
    expect(screen.getByText('Needs help')).toBeInTheDocument();
  });

  it('shows overdue in place of the open status', () => {
    render(<AssignmentStatusChips row={{ status: 'in_progress', overdue: true }} />);
    expect(screen.getByText('Overdue')).toBeInTheDocument();
    expect(screen.queryByText('In progress')).toBeNull();
  });
});

function SortDemo({ rows }) {
  const { rows: sorted, headerProps } = useSortable(rows, { n: (r) => r.n, name: (r) => r.name });
  return (
    <>
      <button {...headerProps('n')}>N</button>
      <ul>{sorted.map((r) => <li key={r.name}>{r.name}</li>)}</ul>
    </>
  );
}

describe('useSortable', () => {
  it('sorts ascending, then descending, with nulls last', () => {
    render(<SortDemo rows={[{ name: 'b', n: 2 }, { name: 'x', n: null }, { name: 'a', n: 1 }]} />);
    const names = () => screen.getAllByRole('listitem').map((li) => li.textContent);
    expect(names()).toEqual(['b', 'x', 'a']);
    fireEvent.click(screen.getByRole('button', { name: 'N' }));
    expect(names()).toEqual(['a', 'b', 'x']);
    fireEvent.click(screen.getByRole('button', { name: 'N' }));
    expect(names()).toEqual(['b', 'a', 'x']);
  });
});

describe('TeacherAssignments delete', () => {
  it('asks before deleting, and only deletes on confirm', async () => {
    apiFetch.mockImplementation(async (url, opts) => (
      opts?.method === 'DELETE'
        ? json({ ok: true })
        : json({ assignments: [{ id: 4, title: 'HW 1' }] })
    ));
    renderWithClient(<TeacherAssignments onCreate={() => {}} onOpen={() => {}} onEdit={() => {}} />);

    fireEvent.click(await screen.findByRole('button', { name: 'Actions for HW 1' }));
    fireEvent.click(screen.getByRole('menuitem', { name: 'Delete' }));
    const dialog = screen.getByRole('dialog', { name: 'Delete "HW 1"?' });

    fireEvent.click(within(dialog).getByRole('button', { name: 'Cancel' }));
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(apiFetch).not.toHaveBeenCalledWith('/assignments/4/', { method: 'DELETE' });

    fireEvent.click(screen.getByRole('button', { name: 'Actions for HW 1' }));
    fireEvent.click(screen.getByRole('menuitem', { name: 'Delete' }));
    fireEvent.click(screen.getByRole('button', { name: 'Delete assignment' }));
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith('/assignments/4/', { method: 'DELETE' }));
  });
});

describe('TeacherAssignments list', () => {
  const future = new Date(Date.now() + 3 * 86400000).toISOString();
  const past = new Date(Date.now() - 3 * 86400000).toISOString();
  const LIST = {
    assignments: [
      {
        id: 1, title: 'Unit 4 review', deck_size: 12, max_cards: 18, allow_late: true, topic_count: 5,
        classes: [{ class_id: 3, class_name: 'P3', due_at: future }, { class_id: 5, class_name: 'P5', due_at: future }],
        next_due_at: future,
        counts: { assigned: 24, done: 12, in_progress: 8, not_started: 3, overdue: 0, needs_help: 2 },
      },
      {
        id: 2, title: 'Unit 3 warm-up', deck_size: 10, max_cards: 15, allow_late: false, topic_count: 2,
        classes: [{ class_id: 3, class_name: 'P3', due_at: past }], next_due_at: past,
        counts: { assigned: 12, done: 10, in_progress: 2, not_started: 0, overdue: 2, needs_help: 0 },
      },
    ],
  };

  it('shows classes, due date, completion and spelled-out flags per row, by status tab', async () => {
    apiFetch.mockResolvedValue(json(LIST));
    renderWithClient(<TeacherAssignments onCreate={() => {}} onOpen={() => {}} onEdit={() => {}} />);

    const row = (await screen.findByRole('button', { name: 'Unit 4 review' })).closest('tr');
    expect(within(row).getByText('P3')).toBeInTheDocument();
    expect(within(row).getByText('P5')).toBeInTheDocument();
    expect(within(row).getByText('12/24')).toBeInTheDocument();
    expect(within(row).getByText('2 need help')).toBeInTheDocument();
    expect(within(row).getByText('3 not started')).toBeInTheDocument();
    expect(within(row).getByText(/5 topics · 12–18 cards/)).toBeInTheDocument();
    // Past-due work sits on its own tab.
    expect(screen.queryByText('Unit 3 warm-up')).toBeNull();
    fireEvent.click(screen.getByRole('tab', { name: /Past due/ }));
    const old = screen.getByRole('button', { name: 'Unit 3 warm-up' }).closest('tr');
    expect(within(old).getByText('2 overdue')).toBeInTheDocument();
  });

  it('duplicates an assignment and opens the copy to edit', async () => {
    apiFetch.mockImplementation(async (url, opts) => (
      opts?.method === 'POST' ? json({ id: 9, title: 'Unit 4 review (copy)' }) : json(LIST)
    ));
    const onEdit = vi.fn();
    renderWithClient(<TeacherAssignments onCreate={() => {}} onOpen={() => {}} onEdit={onEdit} />);
    fireEvent.click(await screen.findByRole('button', { name: 'Actions for Unit 4 review' }));
    fireEvent.click(screen.getByRole('menuitem', { name: 'Duplicate' }));
    await waitFor(() => expect(onEdit).toHaveBeenCalledWith(9));
    expect(apiFetch).toHaveBeenCalledWith('/assignments/1/duplicate/', { method: 'POST' });
  });
});

