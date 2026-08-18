import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithClient } from './test-utils.jsx';

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

const CALENDAR = { year: 2026, month: 8, days: {} };

// The dashboard fires two requests (dashboard + practice-calendar); route the
// shared apiFetch mock by URL so both resolve regardless of call order.
function routeApi(dashboardResponse, calendarResponse = jsonResponse(CALENDAR)) {
  apiFetch.mockImplementation((url) => {
    if (String(url).includes('practice-calendar')) return Promise.resolve(calendarResponse);
    return Promise.resolve(dashboardResponse);
  });
}

// Build N selected topics that all land in the "New" deck (interval 0).
function newTopics(n) {
  return Array.from({ length: n }, (_, i) => ({
    id: i + 1, topic_name: `Topic ${i + 1}`, course_name: 'Algebra',
    repetitions: 0, ease: 2.5, interval: 0, due_date: '2026-08-03',
  }));
}

beforeEach(() => apiFetch.mockReset());

describe('Dashboard', () => {
  it('groups topics into proficiency decks and a "Shown soon" deck', async () => {
    routeApi(jsonResponse(PAYLOAD));
    renderWithClient(<Dashboard />);

    // interval 6 -> "Familiar" deck; upcoming -> "Shown soon"
    await screen.findByText('Linear');
    expect(screen.getByRole('heading', { name: 'Familiar' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Proficient' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Shown soon' })).toBeInTheDocument();
    expect(screen.getByText('Quadratic')).toBeInTheDocument();
  });

  it('shows the selected-topic total next to the pie', async () => {
    routeApi(jsonResponse(PAYLOAD));
    renderWithClient(<Dashboard />);
    await screen.findByText('Linear');
    // Total sits in the legend, not painted on the donut.
    const totalBlock = screen.getByText('topic selected').closest('.dash-legend-total');
    expect(within(totalBlock).getByText('1')).toBeInTheDocument();
  });

  it('previews four topics and expands to show the rest', async () => {
    routeApi(jsonResponse({ selected: newTopics(6), upcoming: [] }));
    renderWithClient(<Dashboard />);

    await screen.findByText('Topic 1');
    expect(screen.getByText('Topic 4')).toBeInTheDocument();
    expect(screen.queryByText('Topic 5')).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /show 2 more/i }));
    expect(screen.getByText('Topic 5')).toBeInTheDocument();
    expect(screen.getByText('Topic 6')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /show less/i }));
    expect(screen.queryByText('Topic 5')).not.toBeInTheDocument();
  });

  it('shows an error when the dashboard fetch fails', async () => {
    routeApi(jsonResponse({}, { ok: false, status: 500 }));
    renderWithClient(<Dashboard />);
    await screen.findByText(/Error: HTTP error! Status: 500/);
  });
});
