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
