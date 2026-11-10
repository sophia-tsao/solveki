import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithClient } from './test-utils.jsx';

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

// The parsed JSON body of the (latest) deck-advance call, or undefined if none.
function advanceBody() {
  const call = apiFetch.mock.calls.filter(([url]) => url.startsWith('/deck/advance/')).at(-1);
  return call && JSON.parse(call[1].body);
}

// Wait until the deck's progress bar reports the student on question `n` of
// `total` (it shows no text; the position is its accessible value).
async function findQuestion(n, total, timeout = 1000) {
  return waitFor(() => {
    const bar = screen.getByRole('progressbar', { name: "Today's practice" });
    expect(bar).toHaveAttribute('aria-valuetext', `Question ${n} of ${total}`);
    return bar;
  }, { timeout });
}

// The deck payload carries no solution; answers are graded by /deck/check/.
const ACTIVE_DECK = {
  problem: 'What is $2+2$?',
  current_number: 1,
  total: 3,
};

// Scripted /deck/check/ verdicts: right, the first miss, and the final miss
// (which reveals the solution).
const CHECK_CORRECT = deckResponse({ correct: true, attempts_left: 2 });
const CHECK_MISS = deckResponse({ correct: false, attempts_left: 1 });
const CHECK_LAST_MISS = deckResponse({ correct: false, attempts_left: 0, solution: '4' });

// The parsed JSON bodies of every answer-check call, in order.
function checkBodies() {
  return apiFetch.mock.calls
    .filter(([url]) => url.startsWith('/deck/check/'))
    .map(([, opts]) => JSON.parse(opts.body));
}

beforeEach(() => {
  apiFetch.mockReset();
  localDay.mockReset();
  localDay.mockReturnValue('2026-07-20');
  localStorage.clear();
});

describe('MathProblem — initial load', () => {
  it('renders the active problem after fetching the deck', async () => {
    apiFetch.mockResolvedValueOnce(deckResponse(ACTIVE_DECK));
    renderWithClient(<MathProblem />);
    const bar = await findQuestion(1, 3);
    // A progress bar, not "1 of 3" text: nothing answered yet of 3 cards.
    expect(bar).toHaveAttribute('aria-valuenow', '0');
    expect(bar).toHaveAttribute('aria-valuemax', '3');
    expect(screen.queryByText(/of 3 questions/)).not.toBeInTheDocument();
    expect(screen.getByText('Attempt 1 of 2')).toBeInTheDocument();
    expect(apiFetch).toHaveBeenCalledWith('/deck/?today=2026-07-20');
  });

  it('shows the no-topics prompt when the deck is empty', async () => {
    apiFetch.mockResolvedValueOnce(deckResponse({ no_topics: true }));
    renderWithClient(<MathProblem />);
    await screen.findByText(/Select topics from the Courses page/);
  });

  it('shows the completion message with pluralized count', async () => {
    apiFetch.mockResolvedValueOnce(deckResponse({ completed: true, total: 5 }));
    renderWithClient(<MathProblem />);
    await screen.findByText(/You've finished all 5 questions for today/);
  });

  it('uses singular wording for a one-question deck', async () => {
    apiFetch.mockResolvedValueOnce(deckResponse({ completed: true, total: 1 }));
    renderWithClient(<MathProblem />);
    await screen.findByText(/all 1 question for today/);
  });

  it('renders an error message when the fetch fails', async () => {
    apiFetch.mockResolvedValueOnce(deckResponse({}, { ok: false, status: 500 }));
    renderWithClient(<MathProblem />);
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

    renderWithClient(<MathProblem />);
    await screen.findByText(/You've finished all 3 questions for today/);
    expect(apiFetch).toHaveBeenCalledTimes(1);

    // Cross midnight into the new local day, then the tab regains focus.
    localDay.mockReturnValue('2026-07-21');
    window.dispatchEvent(new Event('focus'));

    await findQuestion(1, 3);
    expect(apiFetch).toHaveBeenCalledTimes(2);
    expect(apiFetch).toHaveBeenLastCalledWith('/deck/?today=2026-07-21');
  });

  it('reloads on the interval when the day rolls over while the tab stays focused', async () => {
    // A tab left open and focused across midnight never fires focus/visibility,
    // so the periodic timer is the only thing that catches the rollover.
    vi.useFakeTimers();
    try {
      apiFetch
        .mockResolvedValueOnce(deckResponse({ completed: true, total: 3 }))
        .mockResolvedValueOnce(deckResponse(ACTIVE_DECK));

      renderWithClient(<MathProblem />);
      await vi.waitFor(() =>
        expect(screen.getByText(/You've finished all 3 questions for today/)).toBeInTheDocument(),
      );
      expect(apiFetch).toHaveBeenCalledTimes(1);

      // Midnight passes with no focus/visibility event; the timer fires.
      localDay.mockReturnValue('2026-07-21');
      await vi.advanceTimersByTimeAsync(60 * 1000);

      await vi.waitFor(() =>
        expect(apiFetch).toHaveBeenLastCalledWith('/deck/?today=2026-07-21'),
      );
      expect(apiFetch).toHaveBeenCalledTimes(2);
    } finally {
      vi.useRealTimers();
    }
  });

  it('does not reload on refocus within the same day', async () => {
    apiFetch.mockResolvedValueOnce(deckResponse(ACTIVE_DECK));

    renderWithClient(<MathProblem />);
    await findQuestion(1, 3);
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
      .mockResolvedValueOnce(CHECK_CORRECT)
      .mockResolvedValueOnce(
        deckResponse({ ...ACTIVE_DECK, current_number: 2 }),
      );

    renderWithClient(<MathProblem />);
    await findQuestion(1, 3);

    await user.type(screen.getByRole('textbox'), '4');
    await user.click(screen.getByRole('button'));

    // The answer is graded by the backend, for the card on screen.
    expect(checkBodies()).toEqual([{ answer: '4', from_number: 1 }]);
    // "Correct!" interstitial shows before the 900ms advance fires.
    expect(await screen.findByText('Correct!')).toBeInTheDocument();

    // The advance is triggered by a real 900ms setTimeout, so allow headroom.
    expect(await findQuestion(2, 3, 2000)).toBeInTheDocument();
    // A first-attempt correct answer is reported as 'correct_first' so the
    // backend can update the topic's spaced-repetition schedule. `from_number`
    // is the card being left (card 1) so a stale/stray advance can be rejected.
    expect(advanceBody()).toMatchObject({ outcome: 'correct_first', from_number: 1 });
  });

  it('bumps the attempt counter on the first wrong answer', async () => {
    apiFetch.mockResolvedValueOnce(deckResponse(ACTIVE_DECK)).mockResolvedValueOnce(CHECK_MISS);
    const user = userEvent.setup();
    renderWithClient(<MathProblem />);
    await findQuestion(1, 3);

    await user.type(screen.getByRole('textbox'), '99');
    await user.click(screen.getByRole('button'));

    await screen.findByText('Attempt 2 of 2');
    // Only the check — no advance call yet, the user still has an attempt left.
    expect(apiFetch).toHaveBeenCalledTimes(2);
    expect(screen.queryByText(/The answer is/)).not.toBeInTheDocument();
  });

  it('advances after exhausting all attempts and clicking Continue', async () => {
    apiFetch
      .mockResolvedValueOnce(deckResponse(ACTIVE_DECK))
      .mockResolvedValueOnce(CHECK_MISS)
      .mockResolvedValueOnce(CHECK_LAST_MISS)
      .mockResolvedValueOnce(deckResponse({ ...ACTIVE_DECK, current_number: 2 }));
    const user = userEvent.setup();
    renderWithClient(<MathProblem />);
    await findQuestion(1, 3);

    const input = screen.getByRole('textbox');
    const button = screen.getByRole('button');
    await user.type(input, '99');
    await user.click(button); // attempt 1 -> 2
    await screen.findByText('Attempt 2 of 2');
    await user.type(input, '98');
    await user.click(button); // attempt 2 exhausted -> flip (no auto-advance)

    // The card flips to reveal the answer the backend sent with the last miss...
    expect(await screen.findByText('Incorrect...')).toBeInTheDocument();
    expect(screen.getByText('The answer is 4')).toBeInTheDocument();
    // ...and waits — no advance until the student acts (just the two checks).
    expect(apiFetch).toHaveBeenCalledTimes(3);

    // Clicking Continue accepts the miss and advances, reporting 'incorrect'.
    await user.click(screen.getByRole('button', { name: 'Continue' }));
    await waitFor(() =>
      expect(advanceBody()).toMatchObject({ outcome: 'incorrect', from_number: 1 }),
    );
  });

  // Burn both attempts with wrong answers so the card flips to "Incorrect...".
  async function missTwice(user) {
    const input = screen.getByRole('textbox');
    const button = screen.getByRole('button');
    await user.type(input, '99');
    await user.click(button); // attempt 1 -> 2
    await screen.findByText('Attempt 2 of 2');
    await user.type(input, '98');
    await user.click(button); // exhausted -> flip to "Incorrect..."
    expect(await screen.findByText('Incorrect...')).toBeInTheDocument();
  }

  it('reports an issue via "Report issue" and grades the card correct', async () => {
    apiFetch
      .mockResolvedValueOnce(deckResponse(ACTIVE_DECK))
      .mockResolvedValueOnce(CHECK_MISS)
      .mockResolvedValueOnce(CHECK_LAST_MISS)
      .mockResolvedValueOnce(deckResponse({ ...ACTIVE_DECK, current_number: 2 }));
    const user = userEvent.setup();
    renderWithClient(<MathProblem />);
    await findQuestion(1, 3);
    await missTwice(user);
    expect(apiFetch).toHaveBeenCalledTimes(3); // the checks; still waiting on the student

    await user.click(screen.getByRole('button', { name: 'Report issue' }));
    const submit = screen.getByRole('button', { name: 'Submit report' });
    expect(submit).toBeDisabled(); // no reason picked yet
    await user.click(screen.getByRole('radio', { name: /marked incorrect/ }));
    await user.type(screen.getByRole('textbox', { name: 'Describe the problem' }), '98 is right');
    await user.click(submit);

    // The incorrect face eases into "Correct!" and dwells before advancing, so
    // the swap isn't blunt — the advance fires on a real 1400ms setTimeout.
    // Reporting grants full credit ('correct_first'), so a faulty card doesn't
    // drag the topic's schedule down.
    expect(screen.getByText('Correct!')).toBeInTheDocument();
    expect(screen.getByText(/Thanks for the report/)).toBeInTheDocument();
    await waitFor(
      () =>
        expect(advanceBody()).toMatchObject({
          outcome: 'correct_first',
          from_number: 1,
          report: { reason: 'answer_marked_wrong', details: '98 is right', user_answer: '98' },
        }),
      { timeout: 2500 },
    );
  });

  it('requires a description for an "Other" report, and can be cancelled', async () => {
    apiFetch
      .mockResolvedValueOnce(deckResponse(ACTIVE_DECK))
      .mockResolvedValueOnce(CHECK_MISS)
      .mockResolvedValueOnce(CHECK_LAST_MISS);
    const user = userEvent.setup();
    renderWithClient(<MathProblem />);
    await findQuestion(1, 3);
    await missTwice(user);

    await user.click(screen.getByRole('button', { name: 'Report issue' }));
    await user.click(screen.getByRole('radio', { name: 'Other' }));
    const submit = screen.getByRole('button', { name: 'Submit report' });
    expect(submit).toBeDisabled();
    await user.type(screen.getByRole('textbox', { name: 'Describe the problem' }), '   ');
    expect(submit).toBeDisabled(); // whitespace doesn't count
    await user.type(screen.getByRole('textbox', { name: 'Describe the problem' }), 'Typo');
    expect(submit).toBeEnabled();

    // Cancelling returns to Continue / Report issue without advancing.
    await user.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(screen.getByRole('button', { name: 'Continue' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Submit report' })).not.toBeInTheDocument();
    expect(apiFetch).toHaveBeenCalledTimes(3);
  });

  // Regression: the back face used to derive its outcome from the same state
  // that triggered the flip, so clearing that state on advance re-rendered the
  // back to the "Correct!" branch — a flash of "Correct!" while the card
  // rotated back after a wrong answer. The back must keep saying "Incorrect..."
  // through the flip-back onto the next problem.
  it('keeps the incorrect result on the back face while flipping to the next problem', async () => {
    apiFetch
      .mockResolvedValueOnce(deckResponse(ACTIVE_DECK))
      .mockResolvedValueOnce(CHECK_MISS)
      .mockResolvedValueOnce(CHECK_LAST_MISS)
      .mockResolvedValueOnce(deckResponse({ ...ACTIVE_DECK, current_number: 2 }));
    const user = userEvent.setup();
    renderWithClient(<MathProblem />);
    await findQuestion(1, 3);

    const input = screen.getByRole('textbox');
    const button = screen.getByRole('button');
    await user.type(input, '99');
    await user.click(button); // attempt 1 -> 2
    await screen.findByText('Attempt 2 of 2');
    await user.type(input, '98');
    await user.click(button); // exhausted -> flip to "Incorrect..."

    expect(await screen.findByText('Incorrect...')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Continue' }));

    // Advance loads the next problem; the back face must not flash "Correct!".
    await findQuestion(2, 3, 2500);
    expect(screen.queryByText('Correct!')).not.toBeInTheDocument();
    expect(screen.getByText('Incorrect...')).toBeInTheDocument();
  });

  // Regression: the back face once read the live problem's solution, so the
  // displayed answer briefly changed mid-flip. The revealed answer must stay
  // put while the next problem loads.
  it('freezes the revealed answer to the answered problem while flipping away', async () => {
    apiFetch
      .mockResolvedValueOnce(deckResponse(ACTIVE_DECK))
      .mockResolvedValueOnce(CHECK_MISS)
      .mockResolvedValueOnce(CHECK_LAST_MISS) // reveals '4'
      .mockResolvedValueOnce(deckResponse({ ...ACTIVE_DECK, current_number: 2 }));
    const user = userEvent.setup();
    renderWithClient(<MathProblem />);
    await findQuestion(1, 3);

    const input = screen.getByRole('textbox');
    const button = screen.getByRole('button');
    await user.type(input, '99');
    await user.click(button); // attempt 1 -> 2
    await screen.findByText('Attempt 2 of 2');
    await user.type(input, '98');
    await user.click(button); // exhausted -> flip showing "The answer is 4"

    expect(await screen.findByText('The answer is 4')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Continue' }));

    // After the next problem loads, the back face must still show '4'.
    await findQuestion(2, 3, 2500);
    expect(screen.getByText('The answer is 4')).toBeInTheDocument();
  });

  it('offers the step-by-step solution the backend sent with the last miss', async () => {
    const steps = [
      { text: 'Add the two numbers.', math: '2+2=4' },
      { text: 'So the answer is $4$.', math: null },
    ];
    apiFetch
      .mockResolvedValueOnce(deckResponse(ACTIVE_DECK))
      .mockResolvedValueOnce(CHECK_MISS)
      .mockResolvedValueOnce(deckResponse({ correct: false, attempts_left: 0, solution: '4', steps }));
    const user = userEvent.setup();
    renderWithClient(<MathProblem />);
    await findQuestion(1, 3);
    await missTwice(user);

    // Collapsed until asked for, so Continue / Report stay in view.
    expect(screen.queryByText('Add the two numbers.')).not.toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'See step-by-step solution' }));
    expect(screen.getAllByRole('listitem')).toHaveLength(2);
    expect(screen.getByText('Add the two numbers.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Continue' })).toBeInTheDocument();
  });

  it('shows no steps toggle when the problem has no explanation', async () => {
    apiFetch
      .mockResolvedValueOnce(deckResponse(ACTIVE_DECK))
      .mockResolvedValueOnce(CHECK_MISS)
      .mockResolvedValueOnce(CHECK_LAST_MISS);
    const user = userEvent.setup();
    renderWithClient(<MathProblem />);
    await findQuestion(1, 3);
    await missTwice(user);
    expect(screen.queryByRole('button', { name: /step-by-step/ })).not.toBeInTheDocument();
  });
});

describe('MathProblem — server-side checking', () => {
  it('resumes the attempt the backend reports after a reload', async () => {
    apiFetch.mockResolvedValueOnce(deckResponse({ ...ACTIVE_DECK, attempt: 2 }));
    renderWithClient(<MathProblem />);
    expect(await screen.findByText('Attempt 2 of 2')).toBeInTheDocument();
  });

  it('reloads the deck when the answer was for a stale card', async () => {
    const user = userEvent.setup();
    apiFetch
      .mockResolvedValueOnce(deckResponse(ACTIVE_DECK))
      .mockResolvedValueOnce(deckResponse({}, { ok: false, status: 409 }))
      .mockResolvedValueOnce(deckResponse({ ...ACTIVE_DECK, current_number: 2 }));
    const { container } = renderWithClient(<MathProblem />);
    await findQuestion(1, 3);

    await user.type(screen.getByRole('textbox'), '4');
    await user.click(screen.getByRole('button'));

    // No verdict for the stale card; the deck refetch shows the current one.
    expect(await findQuestion(2, 3)).toBeInTheDocument();
    expect(container.querySelector('.math-problem-flipper.flipped')).not.toBeInTheDocument();
    expect(advanceBody()).toBeUndefined();
  });
});

// Finish the single-card deck currently showing by answering it correctly.
// Assumes the next queued apiFetch response is the advance result.
async function finishSingleCardDeck(user) {
  await findQuestion(1, 1);
  await user.type(screen.getByRole('textbox'), '4');
  await user.click(screen.getByRole('button'));
  await screen.findByText(/You've finished all 1 question/, {}, { timeout: 2500 });
}

describe('MathProblem — time on card', () => {
  it('reports the seconds from the card appearing to the answer', async () => {
    let now = 1_000_000;
    const clock = vi.spyOn(Date, 'now').mockImplementation(() => now);
    try {
      apiFetch
        .mockResolvedValueOnce(deckResponse(ACTIVE_DECK))
        .mockResolvedValueOnce(CHECK_CORRECT)
        .mockResolvedValueOnce(deckResponse({ ...ACTIVE_DECK, current_number: 2 }));
      const user = userEvent.setup();
      renderWithClient(<MathProblem />);
      await findQuestion(1, 3);

      now += 12_000; // the student works on the card for 12 seconds
      await user.type(screen.getByRole('textbox'), '4');
      await user.click(screen.getByRole('button'));
      now += 5_000; // the "Correct!" dwell before the advance doesn't count

      await waitFor(
        () => expect(advanceBody()).toEqual({ outcome: 'correct_first', from_number: 1, seconds: 12 }),
        { timeout: 2500 },
      );
    } finally {
      clock.mockRestore();
    }
  });
});

describe('MathProblem — learn more link', () => {
  const VIDEO_URL = 'https://www.youtube.com/watch?v=bAerID24QJ0';
  const DECK_WITH_VIDEO = {
    ...ACTIVE_DECK,
    topic_name: 'Linear Equations',
    learn_more_url: VIDEO_URL,
  };

  it('links the question card to the video the backend sends', async () => {
    apiFetch.mockResolvedValueOnce(deckResponse(DECK_WITH_VIDEO));
    renderWithClient(<MathProblem />);
    await findQuestion(1, 3);

    const link = screen.getByRole('link', { name: /Watch Video/ });
    expect(link).toHaveAttribute('href', VIDEO_URL);
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('omits the link when the backend sends no video, even with a topic name', async () => {
    // The card no longer builds its own search URL from the topic name: without
    // a backend-chosen video there is no link at all.
    apiFetch.mockResolvedValueOnce(
      deckResponse({ ...ACTIVE_DECK, topic_name: 'Linear Equations', learn_more_url: null }),
    );
    renderWithClient(<MathProblem />);
    await findQuestion(1, 3);

    expect(screen.queryByRole('link', { name: /Watch Video/ })).not.toBeInTheDocument();
  });

  it('omits the link for a payload without the field (older deck entries)', async () => {
    apiFetch.mockResolvedValueOnce(deckResponse(ACTIVE_DECK));
    renderWithClient(<MathProblem />);
    await findQuestion(1, 3);

    expect(screen.queryByRole('link', { name: /Watch Video/ })).not.toBeInTheDocument();
  });

  it('keeps the "Watch Video" link on the card when the student gets it wrong', async () => {
    apiFetch
      .mockResolvedValueOnce(deckResponse(DECK_WITH_VIDEO))
      .mockResolvedValueOnce(CHECK_MISS)
      .mockResolvedValueOnce(CHECK_LAST_MISS);
    const user = userEvent.setup();
    renderWithClient(<MathProblem />);
    await findQuestion(1, 3);

    const input = screen.getByRole('textbox');
    const button = screen.getByRole('button', { name: 'Submit' });
    await user.type(input, '99');
    await user.click(button); // attempt 1 -> 2
    await screen.findByText('Attempt 2 of 2');
    await user.type(input, '98');
    await user.click(button); // exhausted -> flip to the incorrect face

    expect(await screen.findByText('Incorrect...')).toBeInTheDocument();
    // Two links now exist (the front face is still mounted behind the flip); the
    // incorrect back face carries its own, both pointing at the topic's video.
    const links = screen.getAllByRole('link', { name: /Watch Video/ });
    expect(links).toHaveLength(2);
    links.forEach((link) => expect(link).toHaveAttribute('href', VIDEO_URL));
  });

  it("switches to the next card's video after advancing", async () => {
    const NEXT_URL = 'https://www.youtube.com/watch?v=_LDR1_Prveo';
    const user = userEvent.setup();
    apiFetch
      .mockResolvedValueOnce(deckResponse(DECK_WITH_VIDEO))
      .mockResolvedValueOnce(CHECK_CORRECT)
      .mockResolvedValueOnce(
        deckResponse({ ...DECK_WITH_VIDEO, current_number: 2, learn_more_url: NEXT_URL }),
      );
    renderWithClient(<MathProblem />);
    await findQuestion(1, 3);

    await user.type(screen.getByRole('textbox'), '4');
    await user.click(screen.getByRole('button'));
    await findQuestion(2, 3, 2000);

    expect(screen.getByRole('link', { name: /Watch Video/ })).toHaveAttribute('href', NEXT_URL);
  });
});

describe('MathProblem — completion confetti', () => {
  it('fires confetti when the student answers the last card', async () => {
    const user = userEvent.setup();
    apiFetch
      .mockResolvedValueOnce(deckResponse({ ...ACTIVE_DECK, total: 1 }))
      .mockResolvedValueOnce(CHECK_CORRECT)
      .mockResolvedValueOnce(deckResponse({ completed: true, total: 1 }));

    const { container } = renderWithClient(<MathProblem />);
    await finishSingleCardDeck(user);

    expect(container.querySelector('.confetti')).toBeInTheDocument();
  });

  // A passive load must never celebrate: only the genuine finish transition
  // (answering the last card, via advanceDeck) fires confetti. The mount fetch,
  // the day-rollover refetch on refocus, a reload of the completed screen, and
  // a topic-change refetch all route through fetchDeck, which never celebrates.
  it('does not fire when a completed deck is loaded passively (mount / reload)', async () => {
    apiFetch.mockResolvedValueOnce(deckResponse({ completed: true, total: 3 }));

    const { container } = renderWithClient(<MathProblem />);
    await screen.findByText(/You've finished all 3 questions/);

    expect(container.querySelector('.confetti')).not.toBeInTheDocument();
  });

  // The core scenario: a student finishes their deck (confetti), raises their
  // questions-per-day, and finishes the newly added cards the SAME day. Each
  // genuine completion must celebrate — there is deliberately no once-per-day
  // suppression, which previously ate the second celebration.
  it('celebrates every genuine finish, including a second one the same day', async () => {
    const user = userEvent.setup();

    // First finish: the original deck.
    apiFetch
      .mockResolvedValueOnce(deckResponse({ ...ACTIVE_DECK, total: 1 }))
      .mockResolvedValueOnce(CHECK_CORRECT)
      .mockResolvedValueOnce(deckResponse({ completed: true, total: 1 }));

    const { container, unmount } = renderWithClient(<MathProblem />);
    await finishSingleCardDeck(user);
    expect(container.querySelector('.confetti')).toBeInTheDocument();
    unmount();

    // Same day: questions-per-day raised, the student finishes the new cards.
    apiFetch
      .mockResolvedValueOnce(deckResponse({ ...ACTIVE_DECK, total: 1 }))
      .mockResolvedValueOnce(CHECK_CORRECT)
      .mockResolvedValueOnce(deckResponse({ completed: true, total: 1 }));

    const { container: c2 } = renderWithClient(<MathProblem />);
    await finishSingleCardDeck(user);
    expect(c2.querySelector('.confetti')).toBeInTheDocument();
  });

  // Full user scenario end to end: reloading (or changing topics) after a
  // celebrated finish reloads the completed deck via fetchDeck, which must stay
  // quiet — the confetti already played on the finish itself.
  it('stays quiet when the completed deck is reopened after celebrating', async () => {
    const user = userEvent.setup();

    // Genuine finish → confetti.
    apiFetch
      .mockResolvedValueOnce(deckResponse({ ...ACTIVE_DECK, total: 1 }))
      .mockResolvedValueOnce(CHECK_CORRECT)
      .mockResolvedValueOnce(deckResponse({ completed: true, total: 1 }));

    const { container, unmount } = renderWithClient(<MathProblem />);
    await finishSingleCardDeck(user);
    expect(container.querySelector('.confetti')).toBeInTheDocument();
    unmount();

    // Reload / topic change: the deck comes back already completed via fetchDeck.
    apiFetch.mockResolvedValueOnce(deckResponse({ completed: true, total: 1 }));

    const { container: c2 } = renderWithClient(<MathProblem />);
    await screen.findByText(/You've finished all 1 question/);
    expect(c2.querySelector('.confetti')).not.toBeInTheDocument();
  });
});

describe('MathProblem — assignment decks', () => {
  it('shows no assignment title on the review deck', async () => {
    apiFetch.mockResolvedValueOnce(deckResponse({ ...ACTIVE_DECK, topic_name: 'Fractions' }));
    const { container } = renderWithClient(<MathProblem />);
    await findQuestion(1, 3);
    expect(container.querySelector('.math-problem-assignment')).toBeNull();
  });

  const CHOICES = [
    { assignment_id: 7, title: 'Unit 3', due_at: null, completion_pct: 40, cards_answered: 2 },
    { assignment_id: 9, title: 'Quiz prep', due_at: null, completion_pct: 0, cards_answered: 0 },
  ];

  it('lists the open assignments to pick from when there are several', async () => {
    const user = userEvent.setup();
    const onOpenAssignment = vi.fn();
    apiFetch.mockResolvedValueOnce(deckResponse({ choose: CHOICES }));
    renderWithClient(<MathProblem onOpenAssignment={onOpenAssignment} />);

    expect(await screen.findByText('Choose an assignment')).toBeInTheDocument();
    expect(screen.getByText('Unit 3')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Keep practicing' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Practice' }));
    expect(onOpenAssignment).toHaveBeenCalledWith(9);
  });

  it("loads the routed assignment's deck and links back to the list", async () => {
    const user = userEvent.setup();
    const onOpenAssignment = vi.fn();
    apiFetch.mockResolvedValueOnce(deckResponse({
      ...ACTIVE_DECK, assignment: { id: 7, title: 'Unit 3', open: true }, open_assignments: 2,
    }));
    renderWithClient(<MathProblem assignmentId={7} onOpenAssignment={onOpenAssignment} />);

    await findQuestion(1, 3);
    expect(apiFetch).toHaveBeenCalledWith('/deck/?today=2026-07-20&assignment=7');
    expect(screen.getByText('Unit 3')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'All assignments' }));
    expect(onOpenAssignment).toHaveBeenCalledWith(null);
  });

  it('leaves the only open assignment for the Assignments page, and a finished one for practice', async () => {
    const user = userEvent.setup();
    const onExit = vi.fn();
    const onOpenAssignment = vi.fn();
    apiFetch.mockResolvedValueOnce(deckResponse({
      ...ACTIVE_DECK, assignment: { id: 7, title: 'Unit 3', open: true }, open_assignments: 1,
    }));
    const { unmount } = renderWithClient(
      <MathProblem assignmentId={7} onExit={onExit} onOpenAssignment={onOpenAssignment} />,
    );
    await findQuestion(1, 3);
    await user.click(screen.getByRole('button', { name: 'Exit assignment' }));
    expect(onExit).toHaveBeenCalled();
    unmount();

    apiFetch.mockResolvedValueOnce(deckResponse({
      ...ACTIVE_DECK, assignment: { id: 8, title: 'Done HW', open: false }, open_assignments: 0,
    }));
    renderWithClient(<MathProblem assignmentId={8} onExit={onExit} onOpenAssignment={onOpenAssignment} />);
    await findQuestion(1, 3);
    await user.click(screen.getByRole('button', { name: 'Exit assignment' }));
    expect(onOpenAssignment).toHaveBeenCalledWith(null);
    expect(onExit).toHaveBeenCalledTimes(1);
  });

  it('keeps answering on the one open assignment the backend picked', async () => {
    const user = userEvent.setup();
    const deck = { ...ACTIVE_DECK, assignment: { id: 7, title: 'Unit 3', open: true }, open_assignments: 1 };
    apiFetch
      .mockResolvedValueOnce(deckResponse(deck))
      .mockResolvedValueOnce(CHECK_CORRECT)
      .mockResolvedValueOnce(deckResponse({ ...deck, current_number: 2 }));
    renderWithClient(<MathProblem />);
    await findQuestion(1, 3);
    // The card names the assignment; with only one open there's no list to go back to.
    expect(screen.getByText('Unit 3')).toHaveClass('math-problem-assignment');
    expect(screen.queryByRole('button', { name: 'All assignments' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Exit assignment' })).toBeInTheDocument();

    await user.type(screen.getByRole('textbox'), '4');
    await user.click(screen.getByRole('button', { name: /submit|check/i }));
    await findQuestion(2, 3, 2000);
    const urls = apiFetch.mock.calls.map(([url]) => url);
    expect(urls).toContain('/deck/check/?today=2026-07-20&assignment=7');
    expect(urls).toContain('/deck/advance/?today=2026-07-20&assignment=7');
  });

});
