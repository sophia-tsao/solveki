import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiFetch, localDay } from './auth.js';
import { BandLegend } from './BandBar.jsx';
import { BandTimeline, TopicBandChart, fmtDay } from './AssignmentCharts.jsx';
import AssignmentProgress from './AssignmentProgress.jsx';
import StruggledTopics from './StruggledTopics.jsx';
import './Teacher.css';

function fmtDue(iso) {
  return iso ? new Date(iso).toLocaleString() : 'No due date';
}

function AssignmentDetail({ assignmentId, onOpenStudent, onBack }) {
  const [classFilter, setClassFilter] = useState('');

  const { data, isPending, error } = useQuery({
    queryKey: ['assignment', assignmentId, 'results', classFilter],
    queryFn: async () => {
      // The local day is sent so the timelines end on the teacher's today.
      const params = new URLSearchParams({ today: localDay() });
      if (classFilter) params.set('class', classFilter);
      const res = await apiFetch(`/assignments/${assignmentId}/results/?${params}`);
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

  const { assignment, topics, struggled, num_students, num_completed, students, timeline_range } = data;
  const classes = assignment.classes || [];

  return (
    <div className="teacher-page">
      {backButton}
      <h1>{assignment.title}</h1>
      {assignment.description && <p className="teacher-card-stat">{assignment.description}</p>}
      <p className="teacher-card-stat">
        {topics.length} topic{topics.length === 1 ? '' : 's'} · at least {assignment.deck_size} cards
        {' '}(up to {assignment.max_cards} for students who struggle)
        {!assignment.allow_late && ' · no late work'}
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

      <div className="ad-summary">
        <div className="teacher-card static">
          <div className="teacher-card-title">Finished</div>
          <div className="teacher-card-stat" style={{ fontSize: '1.5rem' }}>
            {num_completed} / {num_students}
          </div>
        </div>
        <StruggledTopics
          topics={struggled}
          showStudents
          emptyText="No misses on these topics yet."
        />
      </div>

      <h2>Familiarity by topic</h2>
      <p className="teacher-help">Pick a topic to see how many assigned students sit in each band.</p>
      {topics.length === 0
        ? <p className="teacher-empty">This assignment has no topics.</p>
        : <TopicBandChart topics={topics} />}

      <h2>Per-student progress</h2>
      {students.length === 0 ? (
        <p className="teacher-empty">No students are assigned this yet.</p>
      ) : (
        <>
          <p className="teacher-help">
            Each bar shows a student’s familiarity on these topics over time; a new color is a switch
            to a new band. Hover a bar to see the date.
          </p>
          <BandLegend />
          <table className="teacher-table">
            <thead>
              <tr>
                <th>Student</th><th>Completion</th>
                <th>
                  Familiarity over time
                  {timeline_range && (
                    <span className="tl-range">{fmtDay(timeline_range.start)} – {fmtDay(timeline_range.end)}</span>
                  )}
                </th>
                <th>Due</th>
              </tr>
            </thead>
            <tbody>
              {students.map((s) => (
                <tr key={s.student_id}>
                  <td className="clickable" onClick={() => onOpenStudent(s.student_id)}>{s.name}</td>
                  <td><AssignmentProgress row={s} /></td>
                  <td style={{ minWidth: '220px', width: '40%' }}>
                    <BandTimeline segments={s.timeline} range={timeline_range} />
                  </td>
                  <td>{fmtDue(s.due_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}

export default AssignmentDetail;
