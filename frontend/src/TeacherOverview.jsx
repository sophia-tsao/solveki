import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiFetch, localDay } from './auth.js';
import { BandBar } from './BandBar.jsx';
import ProficiencyTrend from './ProficiencyTrend.jsx';
import KpiTile, { Delta } from './ui/KpiTile.jsx';
import PageHeader from './ui/PageHeader.jsx';
import { useSortable } from './ui/useSortable.js';
import { fmtRelativeDue, fmtShortDate, plural } from './ui/format.js';
import './Teacher.css';

// Under this first-try accuracy a topic's figure reads as a problem.
const LOW_ACCURACY = 70;

function greeting(name) {
  const h = new Date().getHours();
  const part = h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening';
  const first = (name || '').trim().split(/\s+/)[0];
  return first ? `${part}, ${first}` : part;
}

function getJson(path) {
  return async () => {
    const res = await apiFetch(path);
    if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
    return res.json();
  };
}

const ICON = { crit: '!', warn: '⚑', info: '◎' };

// One "needs attention" row: what, why, and the one action to take.
function Alert({ item, onOpenStudent, onOpenAssignment, onFollowUp, scopeClass }) {
  let icon = ICON[item.severity];
  let title;
  let detail;
  let action;
  if (item.type === 'student') {
    icon = item.severity === 'crit' ? '!' : '◷';
    title = item.name;
    detail = [
      item.overdue.length > 0 && `${plural(item.overdue.length, 'assignment')} overdue (${item.overdue.join(', ')})`,
      item.inactive_days != null && `no practice in ${item.inactive_days} days`,
    ].filter(Boolean).join(' · ');
    action = { label: 'View student', run: () => onOpenStudent(item.student_id, item.class_id) };
  } else if (item.type === 'needs_help') {
    title = `${item.name} needs help on “${item.title}”`;
    detail = 'Finished at the card cap without getting solid on every topic';
    action = { label: 'View results', run: () => onOpenAssignment(item.assignment_id, { class: item.class_id }) };
  } else if (item.type === 'trouble_spot') {
    title = `Trouble spot: ${item.topic_name}`;
    detail = (
      <>
        {plural(item.students.length, 'student')} missed it lately · {item.accuracy}% first-try accuracy
        {item.students.slice(0, 4).map((s) => <span key={s.id} className="teacher-pill alert-pill">{s.name}</span>)}
        {item.students.length > 4 && <span className="teacher-pill alert-pill">+{item.students.length - 4}</span>}
      </>
    );
    action = { label: 'Assign follow-up', run: () => onFollowUp(item.topic_id, scopeClass || null) };
  } else if (item.type === 'not_started') {
    icon = '◷';
    title = `${plural(item.count, 'student')} haven’t started “${item.title}”`;
    detail = `Due ${fmtRelativeDue(item.due_at, localDay())}, ${fmtShortDate(item.due_at)} · ${item.class_name}`;
    action = {
      label: 'See who',
      run: () => onOpenAssignment(item.assignment_id, { status: 'not_started', class: item.class_id }),
    };
  } else {
    return null;
  }
  return (
    <li className="home-alert">
      <span className={`home-alert-icon ${item.severity}`} aria-hidden="true">{icon}</span>
      <div className="home-alert-text">
        <div className="home-alert-title">{title}</div>
        {detail && <div className="home-alert-detail">{detail}</div>}
      </div>
      <button type="button" className="teacher-button secondary small" onClick={action.run}>{action.label}</button>
    </li>
  );
}

function DueSoon({ items, onOpenAssignment }) {
  if (items.length === 0) return <p className="teacher-empty teacher-box-body">Nothing due in the next week.</p>;
  return (
    <ul className="home-due">
      {items.map((a) => {
        const { counts } = a;
        const pct = counts.assigned ? Math.round((counts.done / counts.assigned) * 100) : 0;
        return (
          <li key={a.id}>
            <button type="button" className="home-due-row" onClick={() => onOpenAssignment(a.id)}>
              <span className="home-due-text">
                <span className="home-due-title">{a.title}</span>
                <span className="row-sub">
                  {a.classes.map((c) => c.class_name).join(', ')} · {fmtShortDate(a.next_due_at)}
                </span>
              </span>
              <span className="teacher-progress home-due-bar">
                <span className="teacher-progress-track" aria-hidden="true">
                  <span className="teacher-progress-fill" style={{ width: `${pct}%` }} />
                </span>
                <span className="teacher-progress-label">{counts.done}/{counts.assigned}</span>
              </span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}

// Newly taught and weak-spot topics as one table, weakest first.
function TopicsToRevisit({ focus }) {
  const byId = new Map();
  for (const t of focus.newly_taught) byId.set(t.topic_id, { ...t, fresh: true });
  for (const t of focus.weak_spots) {
    const prev = byId.get(t.topic_id);
    byId.set(t.topic_id, { ...t, ...prev, accuracy: prev?.accuracy ?? t.accuracy, missed_recent: t.missed_recent });
  }
  const topics = [...byId.values()];
  const { rows, headerProps, ariaSort } = useSortable(topics, {
    name: (t) => t.topic_name.toLowerCase(),
    accuracy: (t) => t.accuracy,
  }, { key: 'accuracy', dir: 'asc' });
  if (topics.length === 0) {
    return (
      <p className="teacher-empty teacher-box-body">
        No new topics in the last {focus.windows.new_days} days and no missed answers lately.
      </p>
    );
  }
  return (
    <table className="teacher-table">
      <thead>
        <tr>
          <th aria-sort={ariaSort('name')}><button {...headerProps('name')}>Topic</button></th>
          <th>Familiarity</th>
          <th aria-sort={ariaSort('accuracy')} className="num"><button {...headerProps('accuracy')}>Accuracy</button></th>
        </tr>
      </thead>
      <tbody>
        {rows.map((t) => (
          <tr key={t.topic_id}>
            <td>
              <span className="home-topic-name">{t.topic_name}</span>
              {t.fresh && <span className="status-chip in_progress home-new-chip">New</span>}
              <span className="row-sub">
                {t.first_assigned ? `First assigned ${fmtShortDate(t.first_assigned)}` : ''}
                {t.first_assigned && t.missed_recent ? ' · ' : ''}
                {t.missed_recent ? `${plural(t.missed_recent, 'student')} missed it lately` : ''}
              </span>
            </td>
            <td style={{ minWidth: '120px' }}>
              {t.proficiency ? <BandBar counts={t.proficiency} /> : <span className="teacher-muted">—</span>}
            </td>
            <td className={`num${t.accuracy != null && t.accuracy < LOW_ACCURACY ? ' teacher-overdue' : ''}`}>
              {t.accuracy == null ? 'Not practiced' : `${t.accuracy}%`}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function TeacherOverview({ userName, onOpenClasses, onOpenStudent, onOpenAssignment, onCreateAssignment, onFollowUp }) {
  // "" = all students across every class; otherwise a specific class id.
  const [scopeClass, setScopeClass] = useState('');
  const today = localDay();
  const scoped = () => {
    const params = new URLSearchParams({ today });
    if (scopeClass) {
      params.set('scope', 'class');
      params.set('class_id', scopeClass);
    }
    return params;
  };

  const overview = useQuery({ queryKey: ['teacher', 'overview'], queryFn: getJson('/teacher/overview/') });
  const summary = useQuery({
    queryKey: ['teacher', 'overview', 'summary', scopeClass],
    queryFn: getJson(`/teacher/overview/summary/?${scoped()}`),
  });
  const focus = useQuery({
    queryKey: ['teacher', 'overview', 'focus', scopeClass],
    queryFn: getJson(`/teacher/overview/focus/?${scoped()}`),
  });

  const data = overview.data;
  const classes = data?.classes || [];
  const selected = classes.find((c) => String(c.id) === scopeClass);
  const dateLabel = new Date(`${today}T00:00`).toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' });

  const header = (
    <PageHeader
      title={greeting(userName)}
      sub={data && `${dateLabel} · ${plural(data.total_students, 'student')} in ${plural(classes.length, 'class', 'classes')}`}
      actions={data && classes.length > 0 && (
        <>
          <select
            className="teacher-select"
            aria-label="Show"
            value={scopeClass}
            onChange={(e) => setScopeClass(e.target.value)}
          >
            <option value="">All classes</option>
            {classes.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <button type="button" className="teacher-button" onClick={() => onCreateAssignment?.()}>+ New assignment</button>
        </>
      )}
    />
  );

  if (overview.isPending) return <div className="teacher-page">{header}<p>Loading…</p></div>;
  if (overview.error) return <div className="teacher-page">{header}<p className="teacher-error">Failed to load overview.</p></div>;
  if (classes.length === 0) {
    return (
      <div className="teacher-page">
        {header}
        <div className="teacher-box teacher-empty-state">
          <h2>Welcome to Solveki</h2>
          <p>Create a class and share its join code. Once students practice, who needs help shows up here.</p>
          <button type="button" className="teacher-button" onClick={() => onOpenClasses?.()}>Create a class</button>
        </div>
      </div>
    );
  }

  const k = summary.data?.kpis;
  const attention = summary.data?.needs_attention || [];
  return (
    <div className="teacher-page">
      {header}

      {summary.error && <p className="teacher-error">Failed to load this week’s summary.</p>}
      {k && (
        <div className="kpi-row">
          <KpiTile
            label="On track for weekly goal"
            value={k.on_track}
            total={k.students}
            note={<>{k.goal_cards ? `Goal ≈ ${k.goal_cards} cards/week · ` : ''}<Delta value={k.on_track - k.on_track_prev} /></>}
          />
          <KpiTile
            label="Cards answered (7 days)"
            value={k.cards_7d}
            note={k.cards_per_active == null ? 'Nobody has practiced yet' : `≈ ${k.cards_per_active} per active student`}
          />
          <KpiTile
            label="First-try accuracy (7 days)"
            value={k.accuracy_7d == null ? '—' : `${k.accuracy_7d}%`}
            note={k.accuracy_7d != null && k.accuracy_prev_7d != null
              ? <Delta value={k.accuracy_7d - k.accuracy_prev_7d} unit=" pts" />
              : 'No answers to compare yet'}
          />
          <KpiTile
            label="Overdue"
            value={k.overdue}
            tone={k.overdue > 0 ? 'crit' : undefined}
            note="student assignments past due"
          />
        </div>
      )}

      <div className="home-grid">
        <section className="teacher-box" aria-labelledby="home-attention">
          <header className="teacher-box-header">
            <h2 id="home-attention">Needs attention</h2>
            {attention.length > 0 && <span className="status-chip overdue">{attention.length}</span>}
            <span className="teacher-muted push">Most urgent first</span>
          </header>
          {summary.isPending ? <p className="teacher-box-body">Loading…</p> : attention.length === 0 ? (
            <p className="teacher-empty teacher-box-body">Nothing needs you right now. Nobody is overdue or stuck.</p>
          ) : (
            <ul className="home-alerts">
              {attention.map((item, i) => (
                <Alert
                  key={`${item.type}-${i}`}
                  item={item}
                  scopeClass={scopeClass}
                  onOpenStudent={onOpenStudent}
                  onOpenAssignment={onOpenAssignment}
                  onFollowUp={onFollowUp}
                />
              ))}
            </ul>
          )}
        </section>
        <section className="teacher-box" aria-labelledby="home-due">
          <header className="teacher-box-header">
            <h2 id="home-due">Due soon</h2>
            <span className="teacher-muted push">Next 7 days</span>
          </header>
          {summary.data && <DueSoon items={summary.data.due_soon} onOpenAssignment={onOpenAssignment} />}
        </section>
      </div>

      <div className="home-grid even">
        <section className="teacher-box" aria-labelledby="home-topics">
          <header className="teacher-box-header">
            <h2 id="home-topics">Topics to revisit</h2>
            <span className="teacher-muted">New topics and weak spots</span>
          </header>
          {focus.isPending && <p className="teacher-box-body">Loading…</p>}
          {focus.error && <p className="teacher-error teacher-box-body">Failed to load topics.</p>}
          {focus.data && <TopicsToRevisit focus={focus.data} />}
        </section>
        <div className="home-trend">
          <ProficiencyTrend
            title={selected ? `Familiarity over time — ${selected.name}` : 'Familiarity over time'}
            description="Topics in each proficiency band, by the students’ average familiarity with each."
            scope={selected ? 'class' : 'all'}
            classId={selected ? selected.id : undefined}
          />
        </div>
      </div>
    </div>
  );
}

export default TeacherOverview;
