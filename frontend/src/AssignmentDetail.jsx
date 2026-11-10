import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiFetch, localDay } from './auth.js';
import { BandLegend } from './BandBar.jsx';
import { BandTimeline, TopicBandChart, fmtDay } from './AssignmentCharts.jsx';
import AssignmentProgress from './AssignmentProgress.jsx';
import StruggledTopics from './StruggledTopics.jsx';
import PageHeader from './ui/PageHeader.jsx';
import StatusCounters from './ui/StatusCounters.jsx';
import Tabs from './ui/Tabs.jsx';
import { AssignmentStatusChips } from './ui/StatusChip.jsx';
import { useSortable } from './ui/useSortable.js';
import { fmtDueDate, fmtLastActive, fmtShortDate, plural } from './ui/format.js';
import './Teacher.css';

// Which status bucket(s) a student falls in, for the counters and filter.
function buckets(s) {
  const out = [s.status];
  if (s.overdue) out.push('overdue');
  if (s.max_reached) out.push('needs_help');
  return out;
}

// Default order: who needs the teacher first.
function attentionRank(s) {
  if (s.overdue) return 0;
  if (s.max_reached) return 1;
  if (s.status === 'not_started') return 2;
  if (s.status === 'in_progress') return 3;
  return 4;
}

function StudentsTable({ students, range, today, showDue, onOpenStudent }) {
  const { rows, headerProps, ariaSort } = useSortable(students, {
    name: (s) => s.name.toLowerCase(),
    status: attentionRank,
    cards: (s) => (s.status === 'done' ? 100 : s.completion_pct ?? 0),
    accuracy: (s) => s.accuracy,
    solid: (s) => s.topics_solid,
    last: (s) => s.last_active,
    due: (s) => s.due_at,
  });
  const sorted = rows === students
    ? [...students].sort((a, b) => attentionRank(a) - attentionRank(b) || a.name.localeCompare(b.name))
    : rows;
  const topicCount = (s) => (s.proficiency ? Object.values(s.proficiency).reduce((a, b) => a + b, 0) : 0);
  const th = (key, label, extra = {}) => (
    <th aria-sort={ariaSort(key)} {...extra}><button {...headerProps(key)}>{label}</button></th>
  );
  return (
    <div className="teacher-box teacher-scroll">
      <table className="teacher-table">
        <thead>
          <tr>
            {th('name', 'Student')}
            {th('status', 'Status')}
            {th('cards', 'Cards')}
            {th('accuracy', 'Accuracy', { className: 'num' })}
            {th('solid', 'Topics solid')}
            <th>
              Familiarity
              {range && <span className="tl-range">{fmtDay(range.start)} – {fmtDay(range.end)}</span>}
            </th>
            {th('last', 'Last active')}
            {showDue && th('due', 'Due')}
          </tr>
        </thead>
        <tbody>
          {sorted.map((s) => (
            <tr key={s.student_id}>
              <td>
                <button type="button" className="teacher-link" onClick={() => onOpenStudent(s.student_id, s.class_id)}>
                  {s.name}
                </button>
              </td>
              <td><AssignmentStatusChips row={s} /></td>
              <td style={{ minWidth: '150px' }}>
                <AssignmentProgress row={s} />
                {s.cards_needed != null && (
                  <span className="row-sub">{s.cards_answered ?? 0} of {s.cards_needed} cards</span>
                )}
              </td>
              <td className="num">{s.accuracy == null ? '—' : `${s.accuracy}%`}</td>
              <td>{s.topics_solid == null ? '—' : `${s.topics_solid} / ${topicCount(s)}`}</td>
              <td style={{ minWidth: '180px', width: '28%' }}>
                <BandTimeline segments={s.timeline} range={range} />
              </td>
              <td className={s.last_active == null ? 'teacher-muted' : undefined}>
                {s.last_active === undefined ? '—' : fmtLastActive(s.last_active, today)}
              </td>
              {showDue && <td>{s.due_at ? fmtShortDate(s.due_at) : '—'}</td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AssignmentDetail({ assignmentId, initialClass = null, initialStatus = null, onOpenStudent, onEdit, onBack }) {
  const [classFilter, setClassFilter] = useState(initialClass ? String(initialClass) : '');
  const [statusFilter, setStatusFilter] = useState(initialStatus || null);
  const [tab, setTab] = useState('students');
  const today = localDay();

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

  const crumbs = [{ label: 'Assignments', onClick: onBack }];
  if (isPending) return <div className="teacher-page"><PageHeader crumbs={crumbs} title="Loading…" /></div>;
  if (error) {
    return (
      <div className="teacher-page">
        <PageHeader crumbs={crumbs} title="Assignment" />
        <p className="teacher-error">Failed to load results.</p>
      </div>
    );
  }

  const { assignment, topics, struggled, students, timeline_range } = data;
  const classes = assignment.classes || [];
  const dues = [...new Set(students.map((s) => s.due_at || ''))];
  const sharedDue = dues.length === 1 ? dues[0] : null;

  const counts = {};
  for (const s of students) for (const b of buckets(s)) counts[b] = (counts[b] || 0) + 1;
  const shown = statusFilter ? students.filter((s) => buckets(s).includes(statusFilter)) : students;

  const sub = [
    plural(topics.length, 'topic'),
    `${assignment.deck_size}–${assignment.max_cards ?? assignment.deck_size} cards`,
    assignment.allow_late ? 'late work allowed' : 'no late work',
    sharedDue !== null && students.length > 0 && (sharedDue ? `due ${fmtDueDate(sharedDue)}` : 'no due date'),
  ].filter(Boolean).join(' · ');

  return (
    <div className="teacher-page">
      <PageHeader
        crumbs={[...crumbs, { label: assignment.title }]}
        title={assignment.title}
        sub={sub}
        actions={(
          <>
            {classes.length > 1 && (
              <select
                className="teacher-select"
                aria-label="Class"
                value={classFilter}
                onChange={(e) => setClassFilter(e.target.value)}
              >
                <option value="">All classes</option>
                {classes.map((c) => (
                  <option key={c.class_id} value={c.class_id}>{c.class_name}</option>
                ))}
              </select>
            )}
            {onEdit && <button type="button" className="teacher-button secondary" onClick={onEdit}>Edit</button>}
          </>
        )}
      />
      {assignment.description && <p className="teacher-muted ad-description">{assignment.description}</p>}
      <p className="teacher-help ad-rule">
        At least {assignment.deck_size} cards (up to {assignment.max_cards ?? assignment.deck_size} for students
        who struggle), spread over the days until it's due.
      </p>

      <StatusCounters total={students.length} counts={counts} value={statusFilter} onChange={setStatusFilter} />

      <Tabs
        label="Results"
        value={tab}
        onChange={setTab}
        tabs={[
          { key: 'students', label: 'Students', count: students.length },
          { key: 'topics', label: 'Topics', count: topics.length },
        ]}
      />

      {tab === 'students' && (students.length === 0 ? (
        <p className="teacher-empty">
          No students are assigned this yet. Assign it to a class from Edit, and students who join get it too.
        </p>
      ) : (
        <>
          <div className="teacher-toolbar">
            <BandLegend />
            {statusFilter && (
              <button type="button" className="teacher-button ghost small push" onClick={() => setStatusFilter(null)}>
                Showing {shown.length} of {students.length} · Clear filter
              </button>
            )}
          </div>
          {shown.length === 0 ? (
            <p className="teacher-empty">No students in this group.</p>
          ) : (
            <StudentsTable
              students={shown}
              range={timeline_range}
              today={today}
              showDue={sharedDue === null}
              onOpenStudent={onOpenStudent}
            />
          )}
        </>
      ))}

      {tab === 'topics' && (
        <div className="ad-topics">
          <StruggledTopics topics={struggled} showStudents emptyText="No misses on these topics yet." />
          <section className="teacher-box teacher-box-body">
            <h2 className="ad-section-title">Familiarity by topic</h2>
            <p className="teacher-help">Pick a topic to see how many assigned students sit in each band.</p>
            {topics.length === 0
              ? <p className="teacher-empty">This assignment has no topics.</p>
              : <TopicBandChart topics={topics} />}
          </section>
        </div>
      )}
    </div>
  );
}

export default AssignmentDetail;
