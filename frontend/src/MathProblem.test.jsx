import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock the network layer so the component's fetch/advance calls are scripted.
// localDay is stubbed to a fixed date so deck-request URLs are deterministic;
// the day-rollover tests override it via mockReturnValue.
vi.mock('./auth.js', () => ({
  apiFetch: vi.fn(),
  localDay: vi.fn(() => '2026-07-20'),
}));
// KaTeX is heavy and irrelevant to behaviour; stub its render to a no-op string.
vi.mock('katex', () => ({ default: { renderToString: () => '' } }));

import { apiFetch, localDay } from './auth.js';
import MathProblem from './MathProblem.jsx';

// Build a Response-like object from a deck payload.
function deckResponse(payload, { ok = true, status = 200 } = {}) {
  return { ok, status, json: async () => payload };
}

const ACTIVE_DECK = {
  problem: 'What is $2+2$?',
  solution: '4',
  current_number: 1,
  total: 3,
};

beforeEach(() => {
  apiFetch.mockReset();
  localDay.mockReset();
  localDay.mockReturnValue('2026-07-20');
  localStorage.clear();
});

describe('MathProblem — initial load', () => {
  it('renders the active problem after fetching the deck', async () => {
    apiFetch.mockResolvedValueOnce(deckResponse(ACTIVE_DECK));
    render(<MathProblem />);
    await screen.findByText('1 of 3 questions');
    expect(screen.getByText('Attempt 1 of 2')).toBeInTheDocument();
    expect(apiFetch).toHaveBeenCalledWith('/deck/?today=2026-07-20');
  });

  it('shows the no-topics prompt when the deck is empty', async () => {
    apiFetch.mockResolvedValueOnce(deckResponse({ no_topics: true }));
    render(<MathProblem />);
    await screen.findByText(/Select topics from the Courses page/);
  });

  it('shows the completion message with pluralized count', async () => {
    apiFetch.mockResolvedValueOnce(deckResponse({ completed: true, total: 5 }));
    render(<MathProblem />);
    await screen.findByText(/You've finished all 5 questions for today/);
  });

  it('uses singular wording for a one-question deck', async () => {
    apiFetch.mockResolvedValueOnce(deckResponse({ completed: true, total: 1 }));
    render(<MathProblem />);
    await screen.findByText(/all 1 question for today/);
  });

  it('renders an error message when the fetch fails', async () => {
    apiFetch.mockResolvedValueOnce(deckResponse({}, { ok: false, status: 500 }));
    render(<MathProblem />);
    await screen.findByText(/Error: HTTP error! Status: 500/);
  });
});

describe('MathProblem — day rollover', () => {
  it('reloads the deck when the local day rolls over and the tab is refocused', async () => {
    // Mounted on the 20th showing yesterday's finished deck, then a fresh deck
    // for the 21st after midnight.
    apiFetch
      .mockResolvedValueOnce(deckResponse({ completed: true, total: 3 }))
      .mockResolvedValueOnce(deckResponse(ACTIVE_DECK));

    render(<MathProblem />);
    await screen.findByText(/You've finished all 3 questions for today/);
    expect(apiFetch).toHaveBeenCalledTimes(1);

    // Cross midnight into the new local day, then the tab regains focus.
    localDay.mockReturnValue('2026-07-21');
    window.dispatchEvent(new Event('focus'));

    await screen.findByText('1 of 3 questions');
    expect(apiFetch).toHaveBeenCalledTimes(2);
    expect(apiFetch).toHaveBeenLastCalledWith('/deck/?today=2026-07-21');
  });

  it('does not reload on refocus within the same day', async () => {
    apiFetch.mockResolvedValueOnce(deckResponse(ACTIVE_DECK));

    render(<MathProblem />);
    await screen.findByText('1 of 3 questions');
    expect(apiFetch).toHaveBeenCalledTimes(1);

    // Same day (localDay unchanged): refocusing must not re-fetch — that would
    // discard local attempt state.
    window.dispatchEvent(new Event('focus'));

    // Give any erroneous fetch a chance to fire before asserting it didn't.
    await Promise.resolve();
    expect(apiFetch).toHaveBeenCalledTimes(1);
  });
});

describe('MathProblem — answering', () => {
  it('advances to the next problem after a correct answer', async () => {
    const user = userEvent.setup();
    apiFetch
      .mockResolvedValueOnce(deckResponse(ACTIVE_DECK))
      .mockResolvedValueOnce(
        deckResponse({ ...ACTIVE_DECK, current_number: 2 }),
      );

    render(<MathProblem />);
    await screen.findByText('1 of 3 questions');

    await user.type(screen.getByRole('textbox'), '4');
    await user.click(screen.getByRole('button'));

    // "Correct!" interstitial shows before the 900ms advance fires.
    expect(screen.getByText('Correct!')).toBeInTheDocument();

    // The advance is triggered by a real 900ms setTimeout, so allow headroom.
    expect(await screen.findByText('2 of 3 questions', {}, { timeout: 2000 })).toBeInTheDocument();
    expect(apiFetch).toHaveBeenCalledWith('/deck/advance/?today=2026-07-20', { method: 'POST' });
  });

  it('bumps the attempt counter on the first wrong answer', async () => {
    apiFetch.mockResolvedValueOnce(deckResponse(ACTIVE_DECK));
    const user = userEvent.setup();
    render(<MathProblem />);
    await screen.findByText('1 of 3 questions');

    await user.type(screen.getByRole('textbox'), '99');
    await user.click(screen.getByRole('button'));

    await screen.findByText('Attempt 2 of 2');
    // No advance call yet — the user still has an attempt left.
    expect(apiFetch).toHaveBeenCalledTimes(1);
  });

  it('advances after exhausting all attempts', async () => {
    apiFetch
      .mockResolvedValueOnce(deckResponse(ACTIVE_DECK))
      .mockResolvedValueOnce(deckResponse({ ...ACTIVE_DECK, current_number: 2 }));
    const user = userEvent.setup();
    render(<MathProblem />);
    await screen.findByText('1 of 3 questions');

    const input = screen.getByRole('textbox');
    const button = screen.getByRole('button');
    await user.type(input, '99');
    await user.click(button); // attempt 1 -> 2
    await screen.findByText('Attempt 2 of 2');
    await user.type(input, '98');
    await user.click(button); // attempt 2 exhausted -> advance

    await waitFor(() =>
      expect(apiFetch).toHaveBeenCalledWith('/deck/advance/?today=2026-07-20', { method: 'POST' }),
    );
  });
});
