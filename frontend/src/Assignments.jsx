import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './auth.js';
import { createLogger } from './logger.js';
import './Assignments.css';

const log = createLogger('assignments');

function formatDue(due) {
  if (!due) return 'No due date';
  return `Due ${new Date(due).toLocaleString()}`;
}

function Assignments({ onStarted }) {
  const queryClient = useQueryClient();
  const [startingId, setStartingId] = useState(null);
  const [error, setError] = useState(null);

  const { data, isPending, error: loadError } = useQuery({
    queryKey: ['assignments', 'mine'],
    queryFn: async () => {
      const res = await apiFetch('/assignments/mine/');
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
  });

  async function start(assignmentId) {
    setError(null);
    setStartingId(assignmentId);
    try {
      // Starting adds the assignment's topics to the student's deck and grows it
      // to the teacher's card count; the student then practices on the normal
      // practice page.
      const res = await apiFetch(`/assignments/${assignmentId}/play/`, { method: 'POST' });
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      // The deck now includes the assigned topics — drop the cached deck so the
      // practice page refetches the grown deck.
      queryClient.invalidateQueries({ queryKey: ['deck'] });
      log.info('Started assignment', assignmentId);
      onStarted();
    } catch (err) {
      setError(err.message);
    } finally {
      setStartingId(null);
    }
  }

  return (
    <div className="assignments-page">
      <h1>Assignments</h1>
      {isPending && <p>Loading…</p>}
      {loadError && <p className="assignments-error">Failed to load assignments.</p>}
      {error && <p className="assignments-error">Couldn’t start: {error}</p>}

      {data && (
        <>
          <section>
            <h2>To do</h2>
            {data.upcoming.length === 0 ? (
              <p className="assignments-empty">Nothing to practice right now.</p>
            ) : (
              <ul className="assignments-list">
                {data.upcoming.map((a) => (
                  <li key={a.assignment_id} className="assignments-item">
                    <div className="assignments-item-main">
                      <span className="assignments-item-title">{a.title}</span>
                      <span className="assignments-item-meta">
                        {a.class_name} · {formatDue(a.due_at)}
                        {a.num_topics > 0 && ` · ${a.num_practiced}/${a.num_topics} topics practiced`}
                        {a.overdue && ' · overdue'}
                      </span>
                    </div>
                    <button
                      className="assignments-item-action"
                      disabled={startingId != null}
                      onClick={() => start(a.assignment_id)}
                    >
                      {startingId === a.assignment_id
                        ? 'Opening…'
                        : a.status === 'in_progress' ? 'Keep practicing' : 'Practice'}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section>
            <h2>Done</h2>
            {data.completed.length === 0 ? (
              <p className="assignments-empty">No completed assignments yet.</p>
            ) : (
              <ul className="assignments-list">
                {data.completed.map((a) => (
                  <li key={a.assignment_id} className="assignments-item">
                    <div className="assignments-item-main">
                      <span className="assignments-item-title">{a.title}</span>
                      <span className="assignments-item-meta">{a.class_name}</span>
                    </div>
                    <button
                      className="assignments-item-action secondary"
                      disabled={startingId != null}
                      onClick={() => start(a.assignment_id)}
                    >
                      {startingId === a.assignment_id ? 'Opening…' : 'Practice again'}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}

export default Assignments;
