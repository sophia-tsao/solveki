import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiFetch, localDay } from './auth.js';
import AssignmentProgress from './AssignmentProgress.jsx';
import { BANDS } from './BandBar.jsx';
import ProficiencyTrend from './ProficiencyTrend.jsx';
import StruggledTopics from './StruggledTopics.jsx';
import KpiTile from './ui/KpiTile.jsx';
import PageHeader from './ui/PageHeader.jsx';
import { AssignmentStatusChips, NEEDS_HELP_HINT } from './ui/StatusChip.jsx';
import { useSortable } from './ui/useSortable.js';
import { daysFrom, fmtDuration, fmtShortDate, plural } from './ui/format.js';
import './Teacher.css';
import './Dashboard.css';

const DAY_LABEL = { completed: 'finished the deck', partial: 'practiced some', none: 'no practice' };

// SM-2 interval → band, matching the backend's `_interval_band`.
function bandOf(interval) {
  if (interval <= 1) return BANDS[0];
  if (interval < 6) return BANDS[1];
  if (interval < 21) return BANDS[2];
  return BANDS[3];
}

function initials(name) {
  const parts = (name || '').trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return '?';
  return (parts[0][0] + (parts.length > 1 ? parts[parts.length - 1][0] : '')).toUpperCase();
}

function getJson(path) {
  return async () => {
    const res = await apiFetch(path);
    if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
    return res.json();
  };
}

// What needs the teacher's attention about this student, named specifically.
function Alerts({ assignments, activity }) {
  const overdue = assignments.filter((a) => a.overdue);
  const needsHelp = assignments.filter((a) => a.max_reached);
  const items = [];
  if (overdue.length) {
    items.push({
      key: 'overdue', tone: 'crit', icon: '!',
      title: `${plural(overdue.length, 'overdue assignment')}`,
      detail: overdue.map((a) => `${a.title}${a.due_at ? ` (due ${fmtShortDate(a.due_at)})` : ''}`).join(' · '),
    });
  }
  if (needsHelp.length) {
    items.push({
      key: 'help', tone: 'warn', icon: '⚑',
      title: `Needs help on ${needsHelp.map((a) => a.title).join(', ')}`,
      detail: NEEDS_HELP_HINT,
    });
  }
  if (activity && activity.week.cards_answered === 0) {
    const last = [...activity.days].reverse().find((d) => d.status !== 'none');
    items.push({
      key: 'quiet', tone: 'warn', icon: '◷',
      title: 'No practice in the last 7 days',
      detail: last ? `Last practiced ${fmtShortDate(last.date)}` : `No practice in the last ${activity.days.length} days`,
    });
  }
  if (items.length === 0) return null;
  return (
    <section className="teacher-box sd-alerts" role="status" aria-label="Needs attention">
      <ul className="home-alerts">
        {items.map((i) => (
          <li key={i.key} className="home-alert">
            <span className={`home-alert-icon ${i.tone}`} aria-hidden="true">{i.icon}</span>
            <div className="home-alert-text">
              <div className="home-alert-title">{i.title}</div>
              <div className="home-alert-detail">{i.detail}</div>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

function PracticeTiles({ activity, benchmarks }) {
  const { days, days_practiced: practiced, streak, week } = activity;
  const today = days[days.length - 1]?.date;
  const vs = (label) => (benchmarks ? ` · class median ${label}` : '');
  return (
    <div className="kpi-row">
      <KpiTile
        label="Consistency"
        value={`${practiced} of last ${days.length} days`}
        note={streak > 0 ? `${streak}-day streak` : 'No current streak'}
      >
        <div className="activity-strip" role="img" aria-label={`Practiced ${practiced} of the last ${days.length} days`}>
          {days.map((d) => (
            <span
              key={d.date}
              className={`activity-day ${d.status}${d.date === today ? ' today' : ''}`}
              title={`${d.date}: ${DAY_LABEL[d.status]}`}
            />
          ))}
        </div>
      </KpiTile>
      <KpiTile
        label="Questions answered (7 days)"
        value={week.cards_answered}
        note={`Last 7 days${vs(benchmarks?.cards_7d_median)}`}
      />
      <KpiTile
        label="Time reviewing (7 days)"
        value={fmtDuration(week.seconds)}
        note={`Last 7 days${benchmarks ? vs(fmtDuration(Math.round(benchmarks.seconds_7d_median))) : ''}`}
      />
      <KpiTile
        label="First-try accuracy (7 days)"
        value={week.accuracy == null ? '—' : `${week.accuracy}%`}
        note={benchmarks?.accuracy_30d_class != null
          ? `Class ${benchmarks.accuracy_30d_class}% over 30 days`
          : 'Right on the first try, last 7 days'}
      />
    </div>
  );
}

// Assignments shown before "View more".
const RECENT_ASSIGNMENTS = 5;

// The student's assignments, most recently assigned first, collapsed to the
// latest few. Clicking a title opens that assignment's report.
function Assignments({ assignments, onOpenAssignment }) {
  const [showAll, setShowAll] = useState(false);
  if (assignments.length === 0) return <p className="teacher-empty teacher-box-body">No assignments yet.</p>;
  const sorted = [...assignments].sort((a, b) => b.assigned_at.localeCompare(a.assigned_at));
  const visible = showAll ? sorted : sorted.slice(0, RECENT_ASSIGNMENTS);
  const hidden = sorted.length - RECENT_ASSIGNMENTS;
  return (
    <>
      <table className="teacher-table">
        <thead>
          <tr><th>Assignment</th><th>Status</th><th>Progress</th><th>Due</th></tr>
        </thead>
        <tbody>
          {visible.map((a) => (
            <tr key={a.assignment_id}>
              <td>
                <button type="button" className="teacher-link" onClick={() => onOpenAssignment?.(a.assignment_id)}>
                  {a.title}
                </button>
                <span className="row-sub">{a.class_name}</span>
              </td>
              <td><AssignmentStatusChips row={a} /></td>
              <td style={{ minWidth: '120px' }}>
                <AssignmentProgress row={a} />
                {a.cards_needed != null && <span className="row-sub">{a.cards_answered ?? 0} of {a.cards_needed} cards</span>}
              </td>
              <td>{a.due_at ? fmtShortDate(a.due_at) : '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {hidden > 0 && (
        <button
          type="button"
          className="teacher-button ghost small sd-more"
          aria-expanded={showAll}
          onClick={() => setShowAll((v) => !v)}
        >
          {showAll ? 'View fewer' : `View more (${hidden})`}
        </button>
      )}
    </>
  );
}

// The student's topics with their band, accuracy and next review, weakest first.
function Topics({ topics, today }) {
  const { rows, headerProps, ariaSort } = useSortable(topics, {
    name: (t) => t.topic_name.toLowerCase(),
    band: (t) => t.interval,
    accuracy: (t) => t.accuracy_30d,
    next: (t) => t.due_date,
  }, { key: 'band', dir: 'asc' });
  if (topics.length === 0) return <p className="teacher-empty teacher-box-body">No topics selected.</p>;
  const th = (key, label, extra = {}) => (
    <th aria-sort={ariaSort(key)} {...extra}><button {...headerProps(key)}>{label}</button></th>
  );
  return (
    <div className="teacher-scroll sd-topics">
      <table className="teacher-table">
        <thead>
          <tr>
            {th('name', 'Topic')}
            {th('band', 'Band')}
            {th('accuracy', 'Accuracy (30d)', { className: 'num' })}
            {th('next', 'Next review')}
          </tr>
        </thead>
        <tbody>
          {rows.map((t) => {
            const band = bandOf(t.interval ?? 0);
            const due = t.due_date ? daysFrom(t.due_date, today) : null;
            return (
              <tr key={t.id}>
                <td>
                  <span className="home-topic-name">{t.topic_name}</span>
                  {t.course_name && <span className="row-sub">{t.course_name}</span>}
                </td>
                <td>
                  <span className="band-chip" style={{ background: band.color, color: band.ink }}>{band.label}</span>
                </td>
                <td className={`num${t.accuracy_30d != null && t.accuracy_30d < 70 ? ' teacher-overdue' : ''}`}>
                  {t.accuracy_30d == null ? '—' : `${t.accuracy_30d}%`}
                </td>
                <td className={due != null && due < 0 ? 'teacher-overdue' : undefined}>
                  {due == null ? '—' : due < 0 ? `Overdue ${-due}d` : due === 0 ? 'Today' : fmtShortDate(t.due_date)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function StudentDetail({ studentId, classId = null, onOpenAssignment, onOpenClasses, onOpenClass, onOpenStudent }) {
  const today = localDay();
  const params = new URLSearchParams({ today });
  if (classId) params.set('class', classId);
  const { data, isPending, error } = useQuery({
    queryKey: ['teacher', 'student', studentId, classId],
    queryFn: getJson(`/teacher/students/${studentId}/?${params}`),
    enabled: studentId != null,
  });

  const classes = data?.classes || [];
  const cls = classes.find((c) => c.id === classId) || classes[0] || null;

  // The class roster, alphabetical, for Prev / Next.
  const roster = useQuery({
    queryKey: ['class', cls?.id, 'students'],
    queryFn: getJson(`/classes/${cls?.id}/students/?today=${today}`),
    enabled: cls != null && onOpenStudent != null,
  });
  const order = [...(roster.data?.students || [])].sort((a, b) => a.name.localeCompare(b.name));
  const at = order.findIndex((s) => s.id === studentId);
  const prev = at > 0 ? order[at - 1] : null;
  const next = at >= 0 && at < order.length - 1 ? order[at + 1] : null;

  const crumbs = [
    { label: 'Classes', onClick: onOpenClasses },
    ...(cls ? [{ label: cls.name, onClick: onOpenClass && (() => onOpenClass(cls.id)) }] : []),
    { label: data?.student.name || 'Student' },
  ];

  if (isPending) return <div className="teacher-page"><PageHeader crumbs={crumbs} title="Loading…" /></div>;
  if (error) {
    return (
      <div className="teacher-page">
        <PageHeader crumbs={crumbs} title="Student" />
        <p className="teacher-error">Failed to load student.</p>
      </div>
    );
  }

  const { student, assignments, activity, benchmarks } = data;
  const sub = [student.email, classes.map((c) => c.name).join(', ')].filter(Boolean).join(' · ');

  return (
    <div className="teacher-page sd-page">
      <PageHeader
        crumbs={crumbs}
        leading={<span className="sd-avatar" aria-hidden="true">{initials(student.name)}</span>}
        title={student.name}
        sub={sub}
        actions={(
          <>
            {order.length > 1 && at >= 0 && (
              <span className="sd-pager">
                <button type="button" className="teacher-button secondary small" disabled={!prev}
                  onClick={() => onOpenStudent(prev.id, cls.id)} aria-label="Previous student">‹ Prev</button>
                <span className="teacher-muted">{at + 1} of {order.length}</span>
                <button type="button" className="teacher-button secondary small" disabled={!next}
                  onClick={() => onOpenStudent(next.id, cls.id)} aria-label="Next student">Next ›</button>
              </span>
            )}
            <button type="button" className="teacher-button secondary" onClick={() => window.print()}>Print report</button>
          </>
        )}
      />

      <Alerts assignments={assignments} activity={activity} />
      {activity && <PracticeTiles activity={activity} benchmarks={benchmarks} />}

      <div className="home-grid even">
        <section className="teacher-box" aria-labelledby="sd-assignments">
          <header className="teacher-box-header">
            <h2 id="sd-assignments">Assignments</h2>
            <span className="teacher-muted">{assignments.length}</span>
          </header>
          <Assignments assignments={assignments} onOpenAssignment={onOpenAssignment} />
        </section>
        <section className="teacher-box" aria-labelledby="sd-topics">
          <header className="teacher-box-header">
            <h2 id="sd-topics">Topics</h2>
            <span className="teacher-muted">weakest first</span>
          </header>
          <Topics topics={data.topics} today={today} />
        </section>
      </div>

      <div className="sd-progress">
        <StruggledTopics topics={data.struggled} emptyText="Nothing stands out — no misses in the last 30 days." />
        <div className="sd-trend">
          <ProficiencyTrend
            title="Familiarity over time"
            description="This student’s topics in each proficiency band."
            scope="student"
            studentId={studentId}
            sideControls
          />
        </div>
      </div>
    </div>
  );
}

export default StudentDetail;
