import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import './MathProblem.css';
import MathProblemDisplay from './MathProblemDisplay.jsx'
import MathProblemResponse from './MathProblemResponse.jsx'
import SolutionSteps from './SolutionSteps.jsx';
import AssignmentChooser from './AssignmentChooser.jsx';
import { apiFetch, localDay } from './auth.js';
import { createLogger } from './logger.js';

const log = createLogger('deck');

// The student's last wrong answer on a revealed card, kept in sessionStorage so
// a report filed after leaving the page and coming back still carries it. Keyed
// by the deck and card so it never rides along with a report on another card.
const LAST_ANSWER_KEY = 'solveki.lastAnswer';
const answerCardKey = (day, scopeId, number) => `${day}:${scopeId ?? ''}:${number}`;
function saveLastAnswer(card, answer) {
  try {
    sessionStorage.setItem(LAST_ANSWER_KEY, JSON.stringify({ card, answer }));
  } catch { /* storage unavailable: the report just goes without it */ }
}
function loadLastAnswer(card) {
  try {
    const saved = JSON.parse(sessionStorage.getItem(LAST_ANSWER_KEY));
    return saved?.card === card ? saved.answer : '';
  } catch {
    return '';
  }
}

function InlineMath({ math }) {
  const html = katex.renderToString(math, { throwOnError: false });
  return <span dangerouslySetInnerHTML={{ __html: html }} />;
}

function renderMixedLatex(str) {
  if (!str) return null;
  return str.split('$').map((segment, i) =>
    i % 2 === 1
      ? <InlineMath key={i} math={segment} />
      : segment
  );
}

// A corner link to a video that teaches the current topic. The backend picks the
// video per topic (see learn_more.py) and sends it as `learn_more_url`; renders
// nothing when it's absent (problems stored before topic attribution, or a topic
// with no curated video), so the card simply omits the link.
function LearnMoreLink({ url }) {
  if (!url) return null;
  return (
    <a
      className="math-problem-learn-more"
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      // The card is clickable (it submits/advances); keep a link click from
      // bubbling into any card-level handler.
      onClick={(e) => e.stopPropagation()}
    >
      Watch Video ↗
    </a>
  );
}

// Reasons a student can pick when reporting a card from its incorrect back
// face. Values match ProblemReport.REASON_CHOICES on the backend; "other"
// requires a typed description.
const REPORT_REASONS = [
  { value: 'answer_marked_wrong', label: 'My answer was correct or equivalent, but was marked incorrect' },
  { value: 'solution_incorrect', label: "Solveki's solution is incorrect" },
  { value: 'other', label: 'Other' },
];

// The "Report issue" form shown on the incorrect back face. Submitting hands
// the chosen reason (and description) to `onSubmit`.
function ReportIssueForm({ onSubmit, onCancel }) {
  const [reason, setReason] = useState(null);
  const [details, setDetails] = useState('');
  const canSubmit = reason !== null && (reason !== 'other' || details.trim() !== '');
  const submit = (e) => {
    e.preventDefault();
    if (canSubmit) onSubmit({ reason, details: details.trim() });
  };
  return (
    <form className="math-problem-report" onSubmit={submit}>
      <fieldset className="math-problem-report-reasons">
        <legend className="math-problem-report-legend">What's wrong with this question?</legend>
        {REPORT_REASONS.map((r) => (
          <label key={r.value} className="math-problem-report-reason">
            <input
              type="radio"
              name="report-reason"
              value={r.value}
              checked={reason === r.value}
              onChange={() => setReason(r.value)}
            />
            {r.label}
          </label>
        ))}
      </fieldset>
      <textarea
        className="math-problem-report-details"
        aria-label="Describe the problem"
        placeholder={reason === 'other' ? 'Describe the problem' : 'Add details (optional)'}
        maxLength={2000}
        rows={3}
        value={details}
        onChange={(e) => setDetails(e.target.value)}
      />
      <div className="math-problem-back-actions">
        <button
          type="button"
          className="math-problem-back-button math-problem-back-secondary"
          onClick={onCancel}
        >
          Cancel
        </button>
        <button
          type="submit"
          className="math-problem-back-button math-problem-back-report"
          disabled={!canSubmit}
        >
          Submit report
        </button>
      </div>
    </form>
  );
}

const CONFETTI_COLORS = ['#2563eb', '#16a34a', '#f59e0b', '#ec4899', '#8b5cf6'];

function Confetti() {
  // Generate the pieces once so they don't reshuffle on re-render.
  const pieces = useMemo(
    () =>
      Array.from({ length: 60 }, (_, i) => ({
        id: i,
        left: Math.random() * 100,
        delay: Math.random() * 0.5,
        duration: 1.8 + Math.random() * 1.2,
        color: CONFETTI_COLORS[i % CONFETTI_COLORS.length],
        rotate: Math.random() * 360,
        drift: (Math.random() - 0.5) * 80,
      })),
    []
  );
  return (
    <div className="confetti" aria-hidden="true">
      {pieces.map((p) => (
        <span
          key={p.id}
          className="confetti-piece"
          style={{
            left: `${p.left}%`,
            backgroundColor: p.color,
            animationDelay: `${p.delay}s`,
            animationDuration: `${p.duration}s`,
            '--confetti-rotate': `${p.rotate}deg`,
            '--confetti-drift': `${p.drift}px`,
          }}
        />
      ))}
    </div>
  );
}

// The deck the practice page shows depends on the student's open assignments
// (see deck.DeckScope): with none, their default deck; with one, its deck; with
// several, a list to pick from (`onOpenAssignment`). `assignmentId` (from the
// route) opens a specific assignment's deck, open or done. `onExit` leaves an
// assignment's deck when the practice page would only reopen it.
function MathProblem({ assignmentId = null, onOpenAssignment, onExit }) {
  const [problem, setProblem] = useState(null);
  const [topicName, setTopicName] = useState(null);
  const [learnMoreUrl, setLearnMoreUrl] = useState(null);
  const [currentNumber, setCurrentNumber] = useState(null);
  const [total, setTotal] = useState(null);
  const [status, setStatus] = useState('loading'); // loading | active | no_topics | completed | choose
  const [choices, setChoices] = useState([]); // the open assignments, when status is 'choose'
  // The assignment ({ id, title, open }) whose deck this is, or null for the default
  // deck, and how many assignments are open (to offer a way back to the list).
  const [deckAssignment, setDeckAssignment] = useState(null);
  const [openAssignments, setOpenAssignments] = useState(0);
  // On a finished assignment deck: cards the assignment still needs on later
  // days, which the student can choose to do now (see finishNow). 0 for none.
  const [cardsLeft, setCardsLeft] = useState(0);
  const [error, setError] = useState(null);
  const [flipped, setFlipped] = useState(false); // true rotates the card to its back
  const [result, setResult] = useState('correct'); // 'correct' | 'incorrect' — back-face content
  const [resultAnswer, setResultAnswer] = useState(null); // solution revealed on the incorrect back face
  const [resultSteps, setResultSteps] = useState([]); // its step-by-step explanation, if the generator gave one
  const [attempt, setAttempt] = useState(1);
  const [overriding, setOverriding] = useState(false); // true while the incorrect face eases into "Correct!"
  const [reporting, setReporting] = useState(false); // true while the incorrect face shows the report form
  const [reported, setReported] = useState(false); // true once a report was filed for the current card
  const [showConfetti, setShowConfetti] = useState(false);
  // When the current card appeared, and how long the student took to answer it
  // (frozen at the final answer, so the dwell on the back face doesn't count).
  // Reported with the advance so teachers can see time spent reviewing.
  const shownAtRef = useRef(Date.now());
  const answerSecondsRef = useRef(0);
  // The student's last (wrong) answer, sent with a report so admins can see it.
  const lastAnswerRef = useRef('');
  const MAX_ATTEMPTS = 2;

  // Fire confetti. Celebration is gated entirely by the `celebrate` flag below
  // (see applyDeck), not by a per-day token: a student who finishes their deck,
  // raises their questions-per-day, and finishes the new cards should be
  // celebrated each time they genuinely complete the deck — even twice in a day.
  const celebrate = useCallback(() => {
    setShowConfetti(true);
    setTimeout(() => setShowConfetti(false), 3500);
  }, []);

  // `celebrate` gates the confetti: only the genuine finish transition (the
  // student answering the last card, via advanceDeck) should fire it. A passive
  // load that happens to land on an already-completed deck — the mount fetch,
  // the day-rollover refetch on refocus, a reload of the completed screen, or a
  // topic change — must not, so reopening a finished deck stays quiet.
  const applyDeck = useCallback((result, { celebrating = false } = {}) => {
    if (result.choose) {
      log.debug(`Choosing between ${result.choose.length} open assignments`);
      setChoices(result.choose);
      setStatus('choose');
      return;
    }
    setDeckAssignment(result.assignment ?? null);
    setOpenAssignments(result.open_assignments ?? 0);
    if (result.no_topics) {
      log.debug('Deck has no selected topics');
      setStatus('no_topics');
      return;
    }
    if (result.completed) {
      // Fall back to the last known total when the payload omits it.
      setTotal((prev) => result.total ?? prev);
      setCardsLeft(result.cards_left ?? 0);
      setStatus('completed');
      log.info('Deck completed');
      if (celebrating) celebrate();
      return;
    }
    log.debug(`Showing question ${result.current_number} of ${result.total}`);
    setProblem(result.problem);
    setTopicName(result.topic_name ?? null);
    setLearnMoreUrl(result.learn_more_url ?? null);
    setCurrentNumber(result.current_number);
    setTotal(result.total);
    // The backend counts attempts, so a reload resumes the one in progress.
    setAttempt(result.attempt ?? 1);
    setOverriding(false);
    setReporting(false);
    setReported(false);
    if (result.revealed) {
      // Its attempts were used up before the student left the page: reopen it
      // on the incorrect back face, solution and steps showing, as they left it.
      setResult('incorrect');
      setResultAnswer(result.revealed.solution?.replace(/\$/g, ''));
      setResultSteps(result.revealed.steps ?? []);
      lastAnswerRef.current = loadLastAnswer(cardKeyRef.current(result.current_number));
      setFlipped(true);
    } else {
      setFlipped(false);
    }
    setStatus('active');
    shownAtRef.current = Date.now();
  }, [celebrate]);

  // Freeze the time spent on the current card at the moment it's answered.
  const stopCardTimer = () => {
    answerSecondsRef.current = Math.round((Date.now() - shownAtRef.current) / 1000);
    return answerSecondsRef.current;
  };

  // The deck belongs to a specific local day. `day` is that day; the deck query
  // is keyed by it, so bumping `day` (a midnight rollover, below) refetches the
  // fresh deck the backend builds for the new day. The client sends its local
  // day because the deck resets at the user's midnight, not the server's UTC one.
  const [day, setDay] = useState(localDay);

  // Once a deck is showing, every call names its assignment, so the student
  // stays on it even if it's the one open assignment that just got finished.
  const scopeId = assignmentId ?? deckAssignment?.id ?? null;
  const scopeParam = scopeId != null ? `&assignment=${scopeId}` : '';
  // The current card's key for the saved last answer (see saveLastAnswer). A
  // ref so applyDeck, defined above, reads the current deck rather than a stale one.
  const cardKeyRef = useRef(null);
  cardKeyRef.current = (number) => answerCardKey(day, scopeId, number);

  const deckQuery = useQuery({
    queryKey: ['deck', day, assignmentId],
    queryFn: async () => {
      const scope = assignmentId != null ? `&assignment=${assignmentId}` : '';
      const response = await apiFetch(`/deck/?today=${day}${scope}`);
      if (!response.ok) {
        const err = new Error(`HTTP error! Status: ${response.status}`);
        err.status = response.status;
        throw err;
      }
      return response.json();
    },
    // Don't keep the deck cached once the page is left: advances and answer
    // checks don't update it, so coming back would briefly show a card from
    // the first load before the refetch lands on the one the student left.
    gcTime: 0,
  });

  // Feed each loaded deck into the card state. A passive load — mount, a day
  // rollover, or reopening a completed deck — never celebrates; only the finish
  // transition in the advance mutation below does (see applyDeck's docstring).
  useEffect(() => {
    if (deckQuery.data) applyDeck(deckQuery.data);
  }, [deckQuery.data, applyDeck]);

  useEffect(() => {
    if (!deckQuery.error) return;
    // An assignment that's gone (or never reached the student), e.g. a deck the
    // Practice link remembered: fall back to the practice page's own deck.
    if (deckQuery.error.status === 404 && assignmentId != null && onOpenAssignment) {
      log.warn(`Assignment ${assignmentId} not found; opening the practice page`);
      onOpenAssignment(null);
      return;
    }
    log.error('Failed to load deck:', deckQuery.error.message);
    setError(deckQuery.error.message);
  }, [deckQuery.error, assignmentId, onOpenAssignment]);

  // `outcome` reports how the card being left was answered ('correct_first' |
  // 'correct_second' | 'incorrect') so the backend can update that topic's
  // spaced-repetition schedule. Omitted for a stray advance with no answer
  // (e.g. the midnight day-rollover advance), which must not grade anything.
  // `fromNumber` is the 1-based card the advance is leaving, captured at the
  // moment the advance is initiated (a click, or when a timer is scheduled).
  // The backend ignores an advance whose `from_number` no longer matches the
  // card it's showing, so a stray leftover timer — e.g. the correct-answer
  // timer from finishing yesterday's last card, firing after the deck has
  // rolled over to today's card 1 — can't step the fresh deck past card 1.
  // `seconds` is how long the student spent answering the card being left.
  // `report`, when set, files a problem report against that card.
  const advanceDeck = useMutation({
    mutationFn: async ({ outcome, fromNumber, seconds, report }) => {
      const body = {};
      if (typeof outcome === 'string') body.outcome = outcome;
      if (typeof fromNumber === 'number') body.from_number = fromNumber;
      if (typeof seconds === 'number') body.seconds = seconds;
      if (report) body.report = report;
      const response = await apiFetch(`/deck/advance/?today=${localDay()}${scopeParam}`, {
        method: 'POST',
        ...(Object.keys(body).length ? { body: JSON.stringify(body) } : {}),
      });
      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
      return response.json();
    },
    // Reaching `completed` here means the student just answered the last card —
    // the one moment worth celebrating.
    onSuccess: (data) => applyDeck(data, { celebrating: true }),
    onError: (err) => {
      log.error('Failed to advance deck:', err.message);
      setError(err.message);
    },
  });

  // "Finish it now": move the rest of the assignment into today's deck, which
  // resumes on the first of the added cards.
  const finishNow = useMutation({
    mutationFn: async () => {
      const response = await apiFetch(`/deck/finish-now/?today=${localDay()}${scopeParam}`, { method: 'POST' });
      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
      return response.json();
    },
    onSuccess: (data) => applyDeck(data),
    onError: (err) => {
      log.error('Failed to finish assignment now:', err.message);
      setError(err.message);
    },
  });

  // Ask the backend to grade `answer` against the current card. The deck
  // payload never carries the solution (it would be readable in dev tools), so
  // this is the only place an answer is checked. Resolves to the parsed
  // response ({ correct, attempts_left, solution? }), or null after a stale
  // card (409), in which case the deck is reloaded to resync.
  const checkAnswer = async (answer, fromNumber) => {
    const response = await apiFetch(`/deck/check/?today=${localDay()}${scopeParam}`, {
      method: 'POST',
      body: JSON.stringify({ answer, from_number: fromNumber }),
    });
    if (response.status === 409) {
      log.warn('Answer was for a stale card; reloading the deck');
      deckQuery.refetch();
      return null;
    }
    if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
    return response.json();
  };

  // The deck resets at the start of each day, but the SPA can sit open across
  // midnight (a student leaves the tab up overnight). Fetching only on mount
  // would leave them staring at yesterday's deck — usually the "come back
  // tomorrow" completion screen. Bumping `day` to the current local day re-keys
  // the deck query so React Query refetches the fresh deck; if the day hasn't
  // changed the state set is a no-op, so nothing refetches and refocusing
  // mid-day never discards local attempt state.
  //
  // Three triggers, because no single one covers every case: refocus and
  // visibility handle a tab that was backgrounded across midnight, and a
  // periodic timer handles a tab that stays focused the whole time (e.g. left
  // open on-screen), which would otherwise never re-check and keep showing
  // yesterday's card.
  useEffect(() => {
    const reloadIfNewDay = () => setDay(localDay());
    const onVisible = () => {
      if (document.visibilityState === 'visible') reloadIfNewDay();
    };
    window.addEventListener('focus', reloadIfNewDay);
    document.addEventListener('visibilitychange', onVisible);
    // Catch a rollover even while the tab stays focused and untouched. A minute
    // is plenty prompt for a day boundary and negligible overhead.
    const interval = setInterval(reloadIfNewDay, 60 * 1000);
    return () => {
      window.removeEventListener('focus', reloadIfNewDay);
      document.removeEventListener('visibilitychange', onVisible);
      clearInterval(interval);
    };
  }, []);

  // Flip the card to reveal the result on its back, then advance once the
  // student has had a beat to read it. advanceDeck() sets `flipped` back to
  // false, flipping the fresh problem to its front. We deliberately leave
  // `result` untouched on the flip back so the back face doesn't flash the
  // other outcome while it rotates out of view.
  const handleCorrect = () => {
    // A first-attempt correct answer grades higher than a second-attempt one.
    const outcome = attempt === 1 ? 'correct_first' : 'correct_second';
    // Capture the card being answered *now*, so if this timer somehow fires
    // after a day-rollover reload, its stale from_number won't match the fresh
    // deck and the backend will ignore it (leaving the student on card 1).
    const from = currentNumber;
    const seconds = stopCardTimer();
    setResult('correct');
    setFlipped(true);
    setTimeout(() => advanceDeck.mutate({ outcome, fromNumber: from, seconds }), 1400);
  };

  // Submit an answer for grading, then route to the correct/incorrect flow.
  // Resolves to the verdict (true/false, or null for none) for the answer box.
  const handleSubmit = async (answer) => {
    let check;
    try {
      check = await checkAnswer(answer, currentNumber);
    } catch (err) {
      log.error('Failed to check answer:', err.message);
      setError(err.message);
      return null;
    }
    if (!check) return null;
    if (check.correct) handleCorrect();
    else handleIncorrect(answer, check);
    return check.correct;
  };

  const handleIncorrect = (answer, check) => {
    lastAnswerRef.current = answer ?? '';
    if (check.attempts_left > 0) {
      setAttempt(MAX_ATTEMPTS - check.attempts_left + 1);
    } else {
      // Out of attempts: flip to show the correct answer. Unlike the correct
      // face (which auto-advances), the incorrect face waits for the student to
      // act — either accepting the miss ("Continue") or reporting the card
      // ("Report issue") if it was marked wrong unfairly or the question itself
      // is faulty. A timed auto-advance would give no time to read the answer
      // or file a report.
      // The backend reveals the solution (and its steps) only now that attempts
      // are used up. They stay in `resultAnswer`/`resultSteps` until the next
      // miss, so the back face keeps showing them while the card rotates to the
      // next problem.
      stopCardTimer();
      saveLastAnswer(cardKeyRef.current(currentNumber), lastAnswerRef.current);
      setResult('incorrect');
      setResultAnswer(check.solution?.replace(/\$/g, ''));
      setResultSteps(check.steps ?? []);
      setFlipped(true);
    }
  };

  // From the incorrect back face: accept the miss and move on.
  const handleAcceptIncorrect = () =>
    advanceDeck.mutate({ outcome: 'incorrect', fromNumber: currentNumber, seconds: answerSecondsRef.current });

  // From the incorrect back face: the student reports the card — their answer
  // was wrongly marked wrong, the solution is wrong, or something else. The
  // report rides along with the advance, which grades the card as a clean
  // correct (full credit) so a faulty card can't drag the topic's schedule
  // down. The back face is already showing, so we can't lean on the flip to
  // soften the swap the way the front-face correct flow does — instead
  // `overriding` fades the "Correct!" content in over the incorrect content,
  // and we hold that beat (matching handleCorrect's dwell) before advancing so
  // the reveal isn't blunt.
  const handleReportSubmit = ({ reason, details }) => {
    log.info('Student reported a problem:', reason);
    // Capture the card being answered now, so a stray timer firing after a
    // day-rollover reload carries a stale from_number the backend will reject.
    const from = currentNumber;
    const seconds = answerSecondsRef.current;
    const report = { reason, details, user_answer: lastAnswerRef.current };
    setReporting(false);
    setReported(true);
    setResult('correct');
    setOverriding(true);
    setTimeout(() => advanceDeck.mutate({ outcome: 'correct_first', fromNumber: from, seconds, report }), 1400);
  };

  if (error) return <div>Error: {error}</div>;

  if (status === 'loading') return null;

  if (status === 'choose') {
    return <AssignmentChooser choices={choices} onOpen={onOpenAssignment} />;
  }

  // On an assignment's cards: its title. The review deck (no assignment) has
  // none, since the student isn't working on an assignment.
  const assignmentLabel = deckAssignment && (
    <span className="math-problem-assignment">{deckAssignment.title}</span>
  );
  // Above an assignment's deck, a way out: to the list when there are others
  // to switch to, otherwise to the practice page's review deck (or the other
  // open assignment). For the only open assignment the practice page would
  // just reopen it, so it leaves to the Assignments page instead.
  const choosing = openAssignments > 1;
  const onlyOpen = deckAssignment?.open && !choosing;
  const scopeBar = deckAssignment && (
    <div className="math-problem-scope">
      <button
        className="math-problem-scope-back"
        onClick={() => (onlyOpen ? onExit() : onOpenAssignment(null))}
      >
        {choosing ? 'Back to assignments' : 'Exit assignment'}
      </button>
    </div>
  );

  if (status === 'no_topics') {
    return (
      <div className="math-problem-card math-problem-card-centered">
        <span className="math-problem-display">Select topics from the Courses page to get started.</span>
      </div>
    );
  }

  if (status === 'completed') {
    return (
      <>
        {scopeBar}
        <div className="math-problem-stack">
          {showConfetti && <Confetti />}
          <div className="math-problem-card math-problem-card-centered">
            {assignmentLabel}
            {cardsLeft > 0 ? (
              <>
                <span className="math-problem-display">
                  You've finished today's {total} question{total === 1 ? '' : 's'} for this assignment.
                </span>
                <span className="math-problem-finish-note">
                  {cardsLeft} more question{cardsLeft === 1 ? ' is' : 's are'} left. You can do them over the
                  days before it's due, or finish the assignment now.
                </span>
                <button
                  className="math-problem-submit math-problem-finish-now"
                  onClick={() => finishNow.mutate()}
                  disabled={finishNow.isPending}
                >
                  Finish it now
                </button>
              </>
            ) : (
              <span className="math-problem-display">
                You've finished all {total} question{total === 1 ? '' : 's'} for today. Come back tomorrow for a new set!
              </span>
            )}
          </div>
        </div>
      </>
    );
  }

  // Cards still remaining after the current one, capped at 3 so the stack
  // stays tidy. Shrinks as the user nears the end of the deck.
  const behindCount = Math.min(3, Math.max(0, total - currentNumber));
  const behindCards = Array.from({ length: behindCount }, (_, i) => (
    <div key={i} className={`math-problem-card math-problem-card-behind behind-${i + 1}`} />
  ));

  return (
    <>
    {scopeBar}
    <div className="math-problem-stack">
      {behindCards}
      {/* The flipper rotates 180° to reveal the back face (the result) when
          `flip` is set. Front holds the problem; back holds the outcome. */}
      <div className={`math-problem-flipper${flipped ? ' flipped' : ''}`}>
        <div className="math-problem-card math-problem-face math-problem-face-front">
          <LearnMoreLink url={learnMoreUrl} />
          <div
            className="math-problem-progress"
            role="progressbar"
            aria-label="Today's practice"
            aria-valuemin={0}
            aria-valuemax={total}
            aria-valuenow={currentNumber - 1}
            aria-valuetext={`Question ${currentNumber} of ${total}`}
          >
            <div
              className="math-problem-progress-fill"
              style={{ width: `${(100 * (currentNumber - 1)) / Math.max(1, total)}%` }}
            />
          </div>
          {assignmentLabel}
          {topicName && <span className="math-problem-topic">{topicName}</span>}
          <MathProblemDisplay problem={renderMixedLatex(problem)} />
          <span className="math-problem-attempt">Attempt {attempt} of {MAX_ATTEMPTS}</span>
          <MathProblemResponse resetKey={`${currentNumber}:${problem}`} onSubmit={handleSubmit} />
        </div>
        <div
          className={`math-problem-card math-problem-face math-problem-face-back ${
            result === 'incorrect' ? 'math-problem-incorrect' : 'math-problem-correct'
          }`}
        >
          {result === 'incorrect' ? (
            <>
              <LearnMoreLink url={learnMoreUrl} />
              <svg className="math-problem-result-icon" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="11" stroke="#dc2626" strokeWidth="1.5" />
                <path d="M8 8l8 8M16 8l-8 8" stroke="#dc2626" strokeWidth="1.75" strokeLinecap="round" />
              </svg>
              <span className="math-problem-incorrect-text">Incorrect...</span>
              <span className="math-problem-answer">The answer is {resultAnswer}</span>
              {/* Keyed per card so each new miss starts with the steps collapsed. */}
              <SolutionSteps key={currentNumber} steps={resultSteps} />
              {reporting ? (
                <ReportIssueForm onSubmit={handleReportSubmit} onCancel={() => setReporting(false)} />
              ) : (
                <div className="math-problem-back-actions">
                  <button
                    className="math-problem-back-button math-problem-back-continue"
                    onClick={handleAcceptIncorrect}
                  >
                    Continue
                  </button>
                  <button
                    className="math-problem-back-button math-problem-back-secondary"
                    onClick={() => setReporting(true)}
                  >
                    Report issue
                  </button>
                </div>
              )}
            </>
          ) : (
            <>
              <svg
                className={`math-problem-result-icon${overriding ? ' math-problem-reveal' : ''}`}
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle cx="12" cy="12" r="11" stroke="#16a34a" strokeWidth="1.5" />
                <path d="M7 12.5l3.2 3.2L17 9" stroke="#16a34a" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <span className={`math-problem-correct-text${overriding ? ' math-problem-reveal' : ''}`}>Correct!</span>
              {reported && (
                <span className="math-problem-report-thanks math-problem-reveal">
                  Thanks for the report! We'll take a look.
                </span>
              )}
            </>
          )}
        </div>
      </div>
    </div>
    </>
  );
}

export default MathProblem;
