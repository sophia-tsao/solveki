import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithClient } from './test-utils.jsx';

vi.mock('./auth.js', () => ({ apiFetch: vi.fn(), localDay: vi.fn(() => '2026-08-16') }));

import { apiFetch } from './auth.js';
import Calendar from './Calendar.jsx';

function jsonResponse(payload, { ok = true, status = 200 } = {}) {
  return { ok, status, json: async () => payload };
}

beforeEach(() => apiFetch.mockReset());

describe('Calendar', () => {
  it('renders the month title and day statuses', async () => {
    apiFetch.mockResolvedValueOnce(jsonResponse({
      year: 2026,
      month: 8,
      days: { '2026-08-03': 'completed', '2026-08-05': 'partial' },
    }));
    renderWithClient(<Calendar />);

    await screen.findByText('August 2026');
    // Days carry a status class the CSS colors.
    const completed = screen.getByText('3');
    expect(completed).toHaveClass('cal-day-completed');
    const partial = screen.getByText('5');
    expect(partial).toHaveClass('cal-day-partial');
    // A day with no record renders as "none".
    expect(screen.getByText('10')).toHaveClass('cal-day-none');
    // Legend is present.
    expect(screen.getByText('Completed')).toBeInTheDocument();
    expect(screen.getByText('Not practiced')).toBeInTheDocument();
  });

  it('marks today', async () => {
    apiFetch.mockResolvedValueOnce(jsonResponse({ year: 2026, month: 8, days: {} }));
    renderWithClient(<Calendar />);
    // localDay() is mocked to 2026-08-16.
    const today = await screen.findByText('16');
    expect(today).toHaveClass('cal-today');
  });

  it('shows an error when the fetch fails', async () => {
    apiFetch.mockResolvedValueOnce(jsonResponse({}, { ok: false, status: 500 }));
    renderWithClient(<Calendar />);
    await screen.findByText(/Error: HTTP error! Status: 500/);
  });
});
