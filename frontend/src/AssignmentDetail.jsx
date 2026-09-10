import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiFetch } from './auth.js';
import { LEVEL_COLOR } from './TopicProgress.jsx';
import './Teacher.css';

// The four proficiency bands, in progression order, sharing the dashboard's
// color system (`young`/`mature` are its internal keys for Familiar/Proficient).
const BANDS = [
  { key: 'new', label: 'New', color: LEVEL_COLOR.new },
  { key: 'learning', label: 'Learning', color: LEVEL_COLOR.learning },
  { key: 'familiar', label: 'Familiar', color: LEVEL_COLOR.young },
  { key: 'proficient', label: 'Proficient', color: LEVEL_COLOR.mature },
];

function fmtDue(iso) {
  return iso ? new Date(iso).toLocaleString() : 'No due date';
}

// A thin stacked bar of a band-count map, e.g. {new, learning, familiar, proficient}.
function BandBar({ counts }) {
  const total = BANDS.reduce((sum, b) => sum + (counts[b.key] || 0), 0);
  if (total === 0) return <span className="teacher-card-stat">—</span>;
  return (
    <span className="ad-bandbar" role="img" aria-label={BANDS.map((b) => `${b.label}: ${counts[b.key] || 0}`).join(', ')}>
      {BANDS.map((b) => {
        const n = counts[b.key] || 0;
        if (n === 0) return null;
        return <span key={b.key} className="ad-bandbar-seg" style={{ flexGrow: n, background: b.color }} />;
      })}
    </span>
  );
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

  const { assignment, topics, num_students, num_practiced, band_totals, students } = data;
  const classes = assignment.classes || [];

  return (
    <div className="teacher-page">
      {backButton}
      <h1>{assignment.title}</h1>
      {assignment.description && <p className="teacher-card-stat">{assignment.description}</p>}
      <p className="teacher-card-stat">
        {topics.length} topic{topics.length === 1 ? '' : 's'} · deck of {assignment.deck_size} cards
      </p>

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
          <div className="teacher-card-title">Practiced</div>
          <div className="teacher-card-stat" style={{ fontSize: '1.5rem' }}>
            {num_practiced} / {num_students}
          </div>
        </div>
        <div className="teacher-card" style={{ flex: 2 }}>
          <div className="teacher-card-title">Familiarity on assigned topics</div>
          <BandBar counts={band_totals} />
          <ul className="ad-legend">
            {BANDS.map((b) => (
              <li key={b.key}>
                <span className="ad-swatch" style={{ background: b.color }} />
                {b.label} <strong>{band_totals[b.key] || 0}</strong>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <h2>Per-student progress</h2>
      {students.length === 0 ? (
        <p className="teacher-empty">No students are assigned this yet.</p>
      ) : (
        <table className="teacher-table">
          <thead>
            <tr>
              <th>Student</th><th>Practiced</th><th>Familiarity</th><th>Due</th>
            </tr>
          </thead>
          <tbody>
            {students.map((s) => (
              <tr key={s.student_id}>
                <td className="clickable" onClick={() => onOpenStudent(s.student_id)}>{s.name}</td>
                <td>
                  {s.practiced ? 'Yes' : 'Not yet'}
                  {s.overdue && <span className="teacher-overdue"> · overdue</span>}
                </td>
                <td style={{ minWidth: '160px' }}><BandBar counts={s.proficiency} /></td>
                <td>{fmtDue(s.due_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default AssignmentDetail;
