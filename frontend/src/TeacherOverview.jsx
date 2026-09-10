import { useQuery } from '@tanstack/react-query';
import { apiFetch } from './auth.js';
import './Teacher.css';

function pct(acc) {
  return acc == null ? '—' : `${Math.round(acc * 100)}%`;
}

function TeacherOverview({ onOpenClass }) {
  const { data, isPending, error } = useQuery({
    queryKey: ['teacher', 'overview'],
    queryFn: async () => {
      const res = await apiFetch('/teacher/overview/');
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
  });

  return (
    <div className="teacher-page">
      <h1>Overview</h1>
      {isPending && <p>Loading…</p>}
      {error && <p className="teacher-error">Failed to load overview.</p>}
      {data && (
        <>
          <p className="teacher-card-stat">
            {data.total_students} student{data.total_students === 1 ? '' : 's'} across your classes ·
            overall accuracy {pct(data.average_accuracy)}
          </p>
          {data.classes.length === 0 ? (
            <p className="teacher-empty">You haven't created any classes yet.</p>
          ) : (
            <div className="teacher-cards">
              {data.classes.map((c) => (
                <button key={c.id} className="teacher-card" onClick={() => onOpenClass(c.id)}>
                  <div className="teacher-card-title">{c.name}</div>
                  <div className="teacher-card-stat">{c.student_count} students</div>
                  <div className="teacher-card-stat">Avg accuracy: {pct(c.average_accuracy)}</div>
                  <div className="teacher-card-stat">{c.completed_assignments} completed assignments</div>
                </button>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default TeacherOverview;
