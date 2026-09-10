import { useQuery } from '@tanstack/react-query';
import { apiFetch } from './auth.js';
import './Assignments.css';

function formatDue(due) {
  if (!due) return 'No due date';
  return `Due ${new Date(due).toLocaleString()}`;
}

function formatAccuracy(acc) {
  return acc == null ? '—' : `${Math.round(acc * 100)}%`;
}

function Assignments({ onOpen }) {
  const { data, isPending, error } = useQuery({
    queryKey: ['assignments', 'mine'],
    queryFn: async () => {
      const res = await apiFetch('/assignments/mine/');
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
  });

  return (
    <div className="assignments-page">
      <h1>Assignments</h1>
      {isPending && <p>Loading…</p>}
      {error && <p className="assignments-error">Failed to load assignments.</p>}

      {data && (
        <>
          <section>
            <h2>Upcoming</h2>
            {data.upcoming.length === 0 ? (
              <p className="assignments-empty">No upcoming assignments.</p>
            ) : (
              <ul className="assignments-list">
                {data.upcoming.map((a) => (
                  <li key={a.assignment_id} className="assignments-item">
                    <div className="assignments-item-main">
                      <span className="assignments-item-title">{a.title}</span>
                      <span className="assignments-item-meta">{a.class_name} · {formatDue(a.due_at)}</span>
                    </div>
                    <button className="assignments-item-action" onClick={() => onOpen(a.assignment_id)}>
                      {a.status === 'in_progress' ? 'Resume' : 'Start'}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section>
            <h2>Completed</h2>
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
                    <span className="assignments-item-accuracy">{formatAccuracy(a.accuracy)}</span>
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
