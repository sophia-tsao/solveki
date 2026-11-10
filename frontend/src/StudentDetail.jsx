import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiFetch, localDay } from './auth.js';
import AssignmentProgress from './AssignmentProgress.jsx';
import { AssignmentStatusChips } from './ui/StatusChip.jsx';
import { TopicDecks } from './TopicProgress.jsx';
import ProficiencyTrend from './ProficiencyTrend.jsx';
import StruggledTopics from './StruggledTopics.jsx';
import './Teacher.css';
import './Dashboard.css';

function fmtDate(iso) {
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

// A duration in seconds as "1h 5m", "12m" or "45s".
function fmtDuration(seconds) {
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m ? `${h}h ${m}m` : `${h}h`;
}

const DAY_LABEL = { completed: 'finished the deck', partial: 'practiced some', none: 'no practice' };

// How consistently, how much, and how well the student has practiced lately.
function PracticeActivity({ activity }) {
  const { days, days_practiced: practiced, streak, week } = activity;
  const today = days[days.length - 1]?.date;
  return (
    <div className="teacher-cards" style={{ marginTop: '1rem' }}>
      <div className="teacher-card static">
        <div className="teacher-card-title">Consistency</div>
        <div className="teacher-card-big">{practiced} of last {days.length} days</div>
        <div className="teacher-card-stat">
          {streak > 0 ? `${streak}-day streak` : 'No current streak'}
        </div>
        <div className="activity-strip" role="img" aria-label={`Practiced ${practiced} of the last ${days.length} days`}>
          {days.map((d) => (
            <span
              key={d.date}
              className={`activity-day ${d.status}${d.date === today ? ' today' : ''}`}
              title={`${d.date}: ${DAY_LABEL[d.status]}`}
            />
          ))}
        </div>
      </div>
      <div className="teacher-card static">
        <div className="teacher-card-title">Questions answered</div>
        <div className="teacher-card-big">{week.cards_answered}</div>
        <div className="teacher-card-stat">Last 7 days</div>
      </div>
      <div className="teacher-card static">
        <div className="teacher-card-title">Time reviewing</div>
        <div className="teacher-card-big">{fmtDuration(week.seconds)}</div>
        <div className="teacher-card-stat">Last 7 days</div>
      </div>
      <div className="teacher-card static">
        <div className="teacher-card-title">Accuracy</div>
        <div className="teacher-card-big">{week.accuracy == null ? '—' : `${week.accuracy}%`}</div>
        <div className="teacher-card-stat">Right on the first try, last 7 days</div>
      </div>
    </div>
  );
}

// A one-line callout of what needs the teacher's attention, or nothing.
function Attention({ assignments, activity }) {
  const overdue = assignments.filter((a) => a.overdue).length;
  const needsHelp = assignments.filter((a) => a.max_reached).length;
  const items = [];
  if (overdue) items.push(`${overdue} overdue assignment${overdue === 1 ? '' : 's'}`);
  if (needsHelp) {
    items.push(`${needsHelp} assignment${needsHelp === 1 ? '' : 's'} finished without getting solid on every topic`);
  }
  if (activity && activity.week.cards_answered === 0) items.push('no practice in the last 7 days');
  if (items.length === 0) return null;
  return (
    <div className="tg-note warn sd-attention" role="status">
      <span className="tg-note-icon">!</span>
      <span>Needs attention: {items.join(' · ')}</span>
    </div>
  );
}

// Assignments shown before "View more".
const RECENT_ASSIGNMENTS = 3;

// The student's assignments, most recently assigned first, collapsed to the
// latest few. Clicking a row opens that assignment's report.
function Assignments({ assignments, onOpenAssignment }) {
  const [showAll, setShowAll] = useState(false);
  if (assignments.length === 0) return <p className="teacher-empty">No assignments yet.</p>;
  const sorted = [...assignments].sort((a, b) => b.assigned_at.localeCompare(a.assigned_at));
  const visible = showAll ? sorted : sorted.slice(0, RECENT_ASSIGNMENTS);
  const hidden = sorted.length - RECENT_ASSIGNMENTS;
  return (
    <>
      <table className="teacher-table">
        <thead>
          <tr><th>Assignment</th><th>Class</th><th>Due</th><th>Status</th><th>Completion</th></tr>
        </thead>
        <tbody>
          {visible.map((a) => (
            <tr
              key={a.assignment_id}
              className="sd-row-link"
              onClick={() => onOpenAssignment(a.assignment_id)}
            >
              <td className="clickable">{a.title}</td>
              <td>{a.class_name}</td>
              <td>{a.due_at ? fmtDate(a.due_at) : '—'}</td>
              <td><AssignmentStatusChips row={a} /></td>
              <td><AssignmentProgress row={a} /></td>
            </tr>
          ))}
        </tbody>
      </table>
      {hidden > 0 && (
        <button
          type="button"
          className="deck-toggle"
          aria-expanded={showAll}
          onClick={() => setShowAll((v) => !v)}
        >
          {showAll ? 'View fewer' : `View more (${hidden})`}
        </button>
      )}
    </>
  );
}

function StudentDetail({ studentId, onOpenAssignment }) {
  const { data, isPending, error } = useQuery({
    queryKey: ['teacher', 'student', studentId],
    queryFn: async () => {
      const res = await apiFetch(`/teacher/students/${studentId}/?today=${localDay()}`);
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
    enabled: studentId != null,
  });

  if (isPending) return <div className="teacher-page"><p>Loading…</p></div>;
  if (error) return <div className="teacher-page"><p className="teacher-error">Failed to load student.</p></div>;

  return (
    <div className="teacher-page">
      <h1>{data.student.name}</h1>
      <p className="teacher-card-stat">{data.student.email}</p>
      <Attention assignments={data.assignments} activity={data.activity} />

      <h2>Practice</h2>
      {data.activity && <PracticeActivity activity={data.activity} />}

      <h2>Proficiency</h2>
      {/* Weak spots beside the trend, then where every topic stands now. */}
      <div className="sd-progress">
        <div>
          <StruggledTopics
            topics={data.struggled || []}
            emptyText="Nothing stands out — no misses in the last 30 days."
          />
        </div>
        <div className="sd-trend">
          <ProficiencyTrend
            title="Familiarity over time"
            description="This student's topics in each proficiency band, day by day."
            scope="student"
            studentId={data.student.id}
            sideControls
          />
        </div>
      </div>
      {data.topics.length === 0 ? (
        <p className="teacher-empty">No topics selected.</p>
      ) : (
        <TopicDecks
          selected={data.topics}
          upcoming={data.upcoming || []}
          description="Every selected topic, grouped by how well it's been learned."
        />
      )}

      <h2>Assignments</h2>
      <Assignments assignments={data.assignments} onOpenAssignment={onOpenAssignment} />
    </div>
  );
}

export default StudentDetail;
