import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

vi.mock('./auth.js', () => ({ apiFetch: vi.fn(), localDay: vi.fn(() => '2026-08-03') }));

import { apiFetch } from './auth.js';
import Dashboard from './Dashboard.jsx';

function jsonResponse(payload, { ok = true, status = 200 } = {}) {
  return { ok, status, json: async () => payload };
}

const PAYLOAD = {
  selected: [
    {
      id: 1, topic_name: 'Linear', course_name: 'Algebra',
      repetitions: 2, ease: 2.36, interval: 6, due_date: '2026-08-09',
    },
  ],
  upcoming: [
    {
      id: 2, topic_name: 'Quadratic', course_name: 'Algebra',
      repetitions: 0, ease: 2.5, interval: 0, due_date: '2026-08-03',
    },
  ],
};

beforeEach(() => apiFetch.mockReset());

describe('Dashboard', () => {
  it('renders selected and upcoming topics with their stats', async () => {
    apiFetch.mockResolvedValueOnce(jsonResponse(PAYLOAD));
    render(<Dashboard />);

    await screen.findByText('Linear');
    expect(screen.getByText('Quadratic')).toBeInTheDocument();
    expect(screen.getByText('Selected topics')).toBeInTheDocument();
    expect(screen.getByText('Shown soon')).toBeInTheDocument();
    expect(screen.getByText('2.36')).toBeInTheDocument();
    expect(screen.getByText('6 days')).toBeInTheDocument();
  });

  it('shows an error when the fetch fails', async () => {
    apiFetch.mockResolvedValueOnce(jsonResponse({}, { ok: false, status: 500 }));
    render(<Dashboard />);
    await screen.findByText(/Error: HTTP error! Status: 500/);
  });
});
