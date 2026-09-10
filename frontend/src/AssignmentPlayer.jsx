import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import './MathProblem.css';
import MathProblemDisplay from './MathProblemDisplay.jsx';
import MathProblemResponse from './MathProblemResponse.jsx';
import { renderMixedLatex } from './mathRender.jsx';
import { apiFetch } from './auth.js';
import { createLogger } from './logger.js';

const log = createLogger('assignment-play');
const MAX_ATTEMPTS = 2;

// Plays through one assignment's problems using the same flip-card UI as the
// daily practice deck, but backed by the assignment endpoints. Outcomes are
// recorded per problem (for teacher analytics); the deck's spaced-repetition
// schedule is only touched when the teacher enabled SM-2 (handled server-side).
function AssignmentPlayer({ assignmentId, onDone }) {
  const [problem, setProblem] = useState(null);
  const [topicName, setTopicName] = useState(null);
  const [solution, setSolution] = useState(null);
  const [currentNumber, setCurrentNumber] = useState(null);
  const [total, setTotal] = useState(null);
  const [title, setTitle] = useState('');
  const [status, setStatus] = useState('loading'); // loading | active | completed | empty
  const [emptyReason, setEmptyReason] = useState(null);
  const [error, setError] = useState(null);
  const [flipped, setFlipped] = useState(false);
  const [result, setResult] = useState('correct');
  const [resultAnswer, setResultAnswer] = useState(null);
  const [attempt, setAttempt] = useState(1);

  const apply = useCallback((data) => {
    if (data.title) setTitle(data.title);
    if (data.empty) {
      setEmptyReason(data.reason ?? null);
      setStatus('empty');
      return;
    }
    if (data.completed) {
      setTotal((prev) => data.total ?? prev);
      setStatus('completed');
      return;
    }
    setProblem(data.problem);
    setTopicName(data.topic_name ?? null);
    setSolution(data.solution?.replace(/\$/g, ''));
    setCurrentNumber(data.current_number);
    setTotal(data.total);
    setAttempt(1);
    setFlipped(false);
    setStatus('active');
  }, []);

  const playQuery = useQuery({
    queryKey: ['assignment-play', assignmentId],
    queryFn: async () => {
      const res = await apiFetch(`/assignments/${assignmentId}/play/`);
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
    enabled: assignmentId != null,
  });

  useEffect(() => {
    if (playQuery.data) apply(playQuery.data);
  }, [playQuery.data, apply]);

  useEffect(() => {
    if (playQuery.error) setError(playQuery.error.message);
  }, [playQuery.error]);

  const advance = useMutation({
    mutationFn: async ({ outcome, fromNumber }) => {
      const res = await apiFetch(`/assignments/${assignmentId}/advance/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ outcome, from_number: fromNumber }),
      });
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
    onSuccess: apply,
    onError: (err) => setError(err.message),
  });

  const handleCorrect = () => {
    const outcome = attempt === 1 ? 'correct_first' : 'correct_second';
    const from = currentNumber;
    setResult('correct');
    setFlipped(true);
    setTimeout(() => advance.mutate({ outcome, fromNumber: from }), 1400);
  };

  const handleIncorrect = () => {
    if (attempt < MAX_ATTEMPTS) {
      setAttempt(attempt + 1);
    } else {
      setResult('incorrect');
      setResultAnswer(solution);
      setFlipped(true);
    }
  };

  const handleAcceptIncorrect = () =>
    advance.mutate({ outcome: 'incorrect', fromNumber: currentNumber });

  const handleOverrideCorrect = () => {
    log.info('Student overrode an incorrect grade to correct');
    const from = currentNumber;
    setResult('correct');
    setTimeout(() => advance.mutate({ outcome: 'correct_first', fromNumber: from }), 1400);
  };

  if (error) return <div className="math-problem-card math-problem-card-centered">Error: {error}</div>;
  if (status === 'loading') return null;

  if (status === 'empty') {
    return (
      <div className="math-problem-stack">
        <div className="math-problem-card math-problem-card-centered">
          <span className="math-problem-display">
            {emptyReason === 'no_topics_in_scope'
              ? "This assignment doesn't have any problems for you yet. Select some topics for its course, then open it again."
              : "This assignment has no problems available right now. Please let your teacher know."}
          </span>
          <button className="math-problem-back-button math-problem-back-continue" onClick={onDone}>
            Back to assignments
          </button>
        </div>
      </div>
    );
  }

  if (status === 'completed') {
    return (
      <div className="math-problem-stack">
        <div className="math-problem-card math-problem-card-centered">
          <span className="math-problem-display">
            You've completed {title ? `"${title}"` : 'this assignment'}
            {total ? ` (${total} question${total === 1 ? '' : 's'})` : ''}. Nice work!
          </span>
          <button className="math-problem-back-button math-problem-back-continue" onClick={onDone}>
            Back to assignments
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="math-problem-stack">
      <button className="assignment-play-back" onClick={onDone}>
        ← Back to assignments
      </button>
      <div className={`math-problem-flipper${flipped ? ' flipped' : ''}`}>
        <div className="math-problem-card math-problem-face math-problem-face-front">
          <div className="math-problem-meta">
            <span className="math-problem-progress">{currentNumber} of {total} questions</span>
            <span className="math-problem-attempt">Attempt {attempt} of {MAX_ATTEMPTS}</span>
          </div>
          {title && <span className="math-problem-topic">{title}</span>}
          {topicName && <span className="math-problem-topic">{topicName}</span>}
          <MathProblemDisplay problem={renderMixedLatex(problem)} />
          <MathProblemResponse solution={solution} onCorrect={handleCorrect} onIncorrect={handleIncorrect} />
        </div>
        <div
          className={`math-problem-card math-problem-face math-problem-face-back ${
            result === 'incorrect' ? 'math-problem-incorrect' : 'math-problem-correct'
          }`}
        >
          {result === 'incorrect' ? (
            <>
              <span className="math-problem-incorrect-text">Incorrect...</span>
              <span className="math-problem-answer">The answer is {resultAnswer}</span>
              <div className="math-problem-back-actions">
                <button className="math-problem-back-button math-problem-back-continue" onClick={handleAcceptIncorrect}>
                  Continue
                </button>
                <button className="math-problem-back-button math-problem-back-override" onClick={handleOverrideCorrect}>
                  I got this correct
                </button>
              </div>
            </>
          ) : (
            <span className="math-problem-correct-text">Correct!</span>
          )}
        </div>
      </div>
    </div>
  );
}

export default AssignmentPlayer;
