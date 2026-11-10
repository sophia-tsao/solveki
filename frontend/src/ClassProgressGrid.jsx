import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiFetch, localDay } from './auth.js';
import { BANDS, BAND_NONE } from './BandBar.jsx';
import { fmtLastActive } from './ui/format.js';
import './Teacher.css';

const BAND = Object.fromEntries(BANDS.map((b) => [b.key, b]));
const RANK = { none: 0, new: 1, learning: 2, familiar: 3, proficient: 4 };

const SORTS = [
  { key: 'attention', label: 'Needs attention' },
  { key: 'name', label: 'Name' },
  { key: 'strongest', label: 'Strongest first' },
];

// A student's average band rank across the topics (not started counts as 0).
function strength(student, topics) {
  if (!topics.length) return 0;
  const total = topics.reduce((sum, t) => sum + RANK[student.cells[t.topic_id]?.band ?? 'none'], 0);
  return total / topics.length;
}

const missedCount = (student, topics) => topics.filter((t) => student.cells[t.topic_id]?.missed_recent).length;

/**
 * The class progress grid: one row per student, one column per topic of the
 * picked assignment, each cell the student's band on that topic (with its
 * initial, so it never relies on color alone) and a red ring when they missed
 * it lately. "Hide names" swaps names for "Student N" so it can be projected.
 */
function ClassProgressGrid({ classId, onOpenStudent }) {
  const [assignment, setAssignment] = useState('');
  const [sort, setSort] = useState('attention');
  const [anonymous, setAnonymous] = useState(false);
  const [hover, setHover] = useState(null); // "studentId:topicId"

  const { data, isPending, error } = useQuery({
    queryKey: ['class', classId, 'progress', assignment],
    queryFn: async () => {
      const params = new URLSearchParams({ today: localDay() });
      if (assignment) params.set('assignment', assignment);
      const res = await apiFetch(`/classes/${classId}/progress/?${params}`);
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
    enabled: classId != null,
  });

  if (isPending) return <p>Loading…</p>;
  if (error) return <p className="teacher-error">Failed to load progress.</p>;

  const { topics, students, assignments, topic_summary: summary } = data;
  const today = localDay();
  if (assignments.length === 0) {
    return (
      <div className="teacher-box teacher-empty-state">
        <h2>No progress to show yet</h2>
        <p>Assign work to this class and each student’s standing on its topics appears here.</p>
      </div>
    );
  }

  const ordered = [...students];
  if (sort === 'name') ordered.sort((a, b) => a.name.localeCompare(b.name));
  else if (sort === 'strongest') ordered.sort((a, b) => strength(b, topics) - strength(a, topics));
  else {
    ordered.sort((a, b) => (strength(a, topics) - missedCount(a, topics) * 0.5)
      - (strength(b, topics) - missedCount(b, topics) * 0.5));
  }
  const label = (s) => (anonymous ? `Student ${students.indexOf(s) + 1}` : s.name);

  return (
    <>
      <div className="teacher-toolbar">
        <select
          className="teacher-select"
          aria-label="Topics from"
          value={assignment || data.assignment_id || ''}
          onChange={(e) => setAssignment(e.target.value)}
        >
          {assignments.map((a) => <option key={a.id} value={a.id}>Topics: {a.title}</option>)}
        </select>
        <select className="teacher-select" aria-label="Sort" value={sort} onChange={(e) => setSort(e.target.value)}>
          {SORTS.map((s) => <option key={s.key} value={s.key}>Sort: {s.label}</option>)}
        </select>
        <label className="teacher-check">
          <input type="checkbox" checked={anonymous} onChange={(e) => setAnonymous(e.target.checked)} />
          Hide names (for projecting)
        </label>
        <ul className="ad-legend push" aria-label="Legend">
          {[BAND_NONE, ...BANDS].map((b) => (
            <li key={b.key}><span className="ad-swatch" style={{ background: b.color, boxShadow: b === BAND_NONE ? 'inset 0 0 0 1px #cbd5e1' : undefined }} />{b.label}</li>
          ))}
          <li><span className="ad-swatch cpg-miss-swatch" />Missed lately</li>
        </ul>
      </div>

      {topics.length === 0 ? (
        <p className="teacher-empty">This assignment has no topics.</p>
      ) : students.length === 0 ? (
        <p className="teacher-empty">No students have joined this class yet.</p>
      ) : (
        <div className="teacher-box teacher-scroll cpg-box">
          <table className="cpg">
            <thead>
              <tr>
                <th className="cpg-corner" scope="col"><span className="visually-hidden">Student</span></th>
                {topics.map((t) => (
                  <th key={t.topic_id} className="cpg-topic" scope="col" title={t.topic_name}>
                    <span>{t.topic_name}</span>
                  </th>
                ))}
                <th className="cpg-meta-head" scope="col">Last active</th>
              </tr>
            </thead>
            <tbody>
              {ordered.map((s) => (
                <tr key={s.id}>
                  <th scope="row" className="cpg-student">
                    <button type="button" className="teacher-link" onClick={() => onOpenStudent(s.id)}>{label(s)}</button>
                  </th>
                  {topics.map((t) => {
                    const cell = s.cells[t.topic_id];
                    const band = cell ? BAND[cell.band] : BAND_NONE;
                    const key = `${s.id}:${t.topic_id}`;
                    const text = `${label(s)}, ${t.topic_name}: ${band.label}${cell?.missed_recent ? ', missed lately' : ''}`;
                    return (
                      <td
                        key={t.topic_id}
                        className={`cpg-cell${cell?.missed_recent ? ' miss' : ''}`}
                        style={{ background: band.color, color: band.ink }}
                        aria-label={text}
                        onMouseEnter={() => setHover(key)}
                        onMouseLeave={() => setHover(null)}
                      >
                        <span aria-hidden="true">{cell ? band.label[0] : '–'}</span>
                        {hover === key && <span className="ad-tooltip cpg-tooltip" role="tooltip">{text}</span>}
                      </td>
                    );
                  })}
                  <td className="cpg-meta">{fmtLastActive(s.last_active, today)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <th scope="row" className="cpg-student cpg-foot-label">% Familiar or better</th>
                {topics.map((t) => (
                  <td key={t.topic_id} className="cpg-summary">
                    {summary[t.topic_id] == null ? '—' : `${summary[t.topic_id]}%`}
                  </td>
                ))}
                <td />
              </tr>
            </tfoot>
          </table>
        </div>
      )}
      <p className="teacher-help">
        Each cell is the student’s spaced-repetition band on that topic, with its first letter. Click a name to open the student.
      </p>
    </>
  );
}

export default ClassProgressGrid;
