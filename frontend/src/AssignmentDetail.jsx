import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiFetch } from './auth.js';
import './Teacher.css';

function pct(acc) {
  return acc == null ? '—' : `${Math.round(acc * 100)}%`;
}

function fmtDuration(seconds) {
  if (seconds == null) return '—';
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

function fmtTime(iso) {
  return iso ? new Date(iso).toLocaleString() : '—';
}

function AssignmentDetail({ assignmentId, onOpenStudent, onBack }) {
  const [classFilter, setClassFilter] = useState('');

  const { data, isPending, error } = useQuery({
    queryKey: ['assignment', assignmentId, 'results', classFilter],
    queryFn: async () => {
      const q = classFilter ? `?class=${classFilter}` : '';
      const res = await apiFetch(`/assignments/${assignmentId}/results/${q}`);
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
    enabled: assignmentId != null,
  });

  const backButton = onBack && (
    <button className="teacher-button secondary teacher-back" onClick={onBack}>
      ← Back to assignments
    </button>
  );

  if (isPending) return <div className="teacher-page">{backButton}<p>Loading…</p></div>;
  if (error) return <div className="teacher-page">{backButton}<p className="teacher-error">Failed to load results.</p></div>;

  const { assignment, average_accuracy, num_submissions, topics_struggled, students } = data;
  const classes = assignment.classes || [];
  const worstAcc = topics_struggled.reduce(
    (max, t) => Math.max(max, t.accuracy == null ? 0 : t.accuracy),
    0
  ) || 1;

  return (
    <div className="teacher-page">
      {backButton}
      <h1>{assignment.title}</h1>
      {assignment.description && <p className="teacher-card-stat">{assignment.description}</p>}

      <div className="teacher-header" style={{ marginTop: '0.5rem' }}>
        <div className="teacher-field" style={{ margin: 0 }}>
          <label>Class</label>
          <select value={classFilter} onChange={(e) => setClassFilter(e.target.value)}>
            <option value="">All classes</option>
            {classes.map((c) => (
              <option key={c.class_id} value={c.class_id}>{c.class_name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="teacher-cards" style={{ marginTop: '1rem' }}>
        <div className="teacher-card">
          <div className="teacher-card-title">Average accuracy</div>
          <div className="teacher-card-stat" style={{ fontSize: '1.5rem' }}>{pct(average_accuracy)}</div>
        </div>
        <div className="teacher-card">
          <div className="teacher-card-title">Submissions</div>
          <div className="teacher-card-stat" style={{ fontSize: '1.5rem' }}>{num_submissions}</div>
        </div>
      </div>

      <h2>Topics most struggled with</h2>
      {topics_struggled.length === 0 ? (
        <p className="teacher-empty">No answers recorded yet.</p>
      ) : (
        <div className="teacher-bars">
          {topics_struggled.map((t) => (
            <div key={t.topic_id} className="teacher-bar-row">
              <span className="teacher-bar-label">{t.topic_name}</span>
              <span className="teacher-bar-track">
                <span
                  className="teacher-bar-fill"
                  style={{ width: `${((t.accuracy == null ? 0 : t.accuracy) / worstAcc) * 100}%` }}
                />
              </span>
              <span className="teacher-bar-value">{pct(t.accuracy)} <small>({t.answered})</small></span>
            </div>
          ))}
        </div>
      )}

      <h2>Per-student results</h2>
      {students.length === 0 ? (
        <p className="teacher-empty">No students have started this assignment.</p>
      ) : (
        <table className="teacher-table">
          <thead>
            <tr>
              <th>Student</th><th>Status</th><th>Accuracy</th><th>Answered</th>
              <th>Began</th><th>Time taken</th>
            </tr>
          </thead>
          <tbody>
            {students.map((s) => (
              <tr key={s.student_id}>
                <td className="clickable" onClick={() => onOpenStudent(s.student_id)}>{s.name}</td>
                <td>{s.status.replace('_', ' ')}</td>
                <td>{pct(s.accuracy)}</td>
                <td>{s.answered}</td>
                <td>{fmtTime(s.started_at)}</td>
                <td>{fmtDuration(s.time_taken_seconds)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default AssignmentDetail;
