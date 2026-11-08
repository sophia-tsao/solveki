import { describe, it, expect, beforeEach, vi } from 'vitest';
import { fireEvent, screen, within } from '@testing-library/react';
import { renderWithClient } from './test-utils.jsx';

vi.mock('./auth.js', () => ({
  apiFetch: vi.fn(),
  localDay: vi.fn(() => '2026-11-05'),
}));

import { apiFetch } from './auth.js';
import ProficiencyTrend from './ProficiencyTrend.jsx';

function json(payload) {
  return { ok: true, status: 200, json: async () => payload };
}

const SERIES = [
  { date: '2026-11-04', new: 4, learning: 2, familiar: 0, proficient: 0 },
  { date: '2026-11-05', new: 2, learning: 1, familiar: 3, proficient: 1 },
];

beforeEach(() => {
  apiFetch.mockReset();
  apiFetch.mockResolvedValue(json({ series: SERIES }));
});

describe('ProficiencyTrend', () => {
  it('draws one stacked bar per day on a topic-count axis', async () => {
    const { container } = renderWithClient(
      <ProficiencyTrend title="Familiarity over time" defaultDays={30} />,
    );

    expect(await screen.findByRole('img', { name: /number of topics in each/ })).toBeInTheDocument();
    expect(screen.getByText('Topics')).toBeInTheDocument();
    // Counts, not percentages, on the axis.
    expect(screen.queryByText('100%')).toBeNull();
    expect(container.querySelectorAll('.ptrend-bar')).toHaveLength(2);
    expect(apiFetch).toHaveBeenCalledWith(expect.stringContaining('days=30'));
  });

  it('shows a bar’s band counts and total on hover', async () => {
    const { container } = renderWithClient(<ProficiencyTrend title="Familiarity over time" />);
    await screen.findByRole('img', { name: /Familiarity over time/ });

    fireEvent.mouseEnter(container.querySelectorAll('.ptrend-hit')[1]);
    const tip = container.querySelector('.ptrend-tooltip');
    expect(within(tip).getByText('Nov 5')).toBeInTheDocument();
    const row = (label) => within(tip).getByText(label).parentElement;
    expect(row('Familiar')).toHaveTextContent('3');
    expect(row('Total')).toHaveTextContent('7');
  });

  it('switches the time frame', async () => {
    renderWithClient(<ProficiencyTrend title="Familiarity over time" defaultDays={30} />);
    await screen.findByRole('img', { name: /Familiarity over time/ });

    fireEvent.change(screen.getByLabelText('Time frame'), { target: { value: '365' } });
    expect(apiFetch).toHaveBeenLastCalledWith(expect.stringContaining('days=365'));
  });
});
