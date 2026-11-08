import { useEffect, useId, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiFetch, localDay } from './auth.js';
import ProficiencyTrend from './ProficiencyTrend.jsx';
import { BandBar, BandLegend } from './BandBar.jsx';
import './Teacher.css';

function plural(n, word) {
  return `${n} ${word}${n === 1 ? '' : 's'}`;
}

function fmtDate(iso) {
  return new Date(`${iso}T00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

// "the past 2 weeks" for whole weeks, else "the past N days".
function pastDays(days) {
  return days % 7 === 0 ? `the past ${plural(days / 7, 'week')}` : `the past ${plural(days, 'day')}`;
}

// Whether `el`'s focus came from the keyboard (browsers without
// :focus-visible count every focus).
function focusVisible(el) {
  try {
    return el.matches(':focus-visible');
  } catch {
    return true;
  }
}

// How long the pointer has to rest on a topic before its detail card opens.
const HOVER_DELAY_MS = 1000;

// A single-fill bar of a topic's first-try accuracy (0-100), averaged per
// student. `showPercent` writes the figure in the bar without resizing it.
function AccuracyBar({ accuracy, showPercent = false }) {
  return (
    <span className="focus-accbar" role="img" aria-label={`Average accuracy: ${accuracy}%`}>
      <span className="focus-accbar-fill" style={{ width: `${accuracy}%` }} />
      {showPercent && (
        <span
          className={`focus-accbar-pct ${accuracy >= 15 ? 'inside' : 'outside'}`}
          style={accuracy >= 15 ? { right: `${100 - accuracy}%` } : { left: `${accuracy}%` }}
          aria-hidden="true"
        >
          {accuracy}%
        </span>
      )}
    </span>
  );
}

// One topic in a focus column: its name over a bar. Resting the pointer on it
// for `HOVER_DELAY_MS` (or tabbing to it) writes the exact figures into the
// bar and opens a detail card just below the row; leaving fades it back out.
function FocusItem({ topic, renderBar, detail }) {
  const [card, setCard] = useState('closed'); // 'closed' | 'open' | 'closing'
  const timer = useRef(null);
  const cardId = useId();

  useEffect(() => () => clearTimeout(timer.current), []);

  function open() {
    clearTimeout(timer.current);
    setCard('open');
  }
  function close() {
    clearTimeout(timer.current);
    setCard((c) => (c === 'open' ? 'closing' : 'closed'));
  }

  return (
    <li
      className="focus-item"
      tabIndex={0}
      aria-describedby={card === 'open' ? cardId : undefined}
      onMouseEnter={() => {
        clearTimeout(timer.current);
        timer.current = setTimeout(open, HOVER_DELAY_MS);
      }}
      onMouseLeave={close}
      onFocus={(e) => {
        // Keyboard focus opens at once; a click's focus waits for the hover delay.
        if (focusVisible(e.currentTarget)) open();
      }}
      onBlur={close}
    >
      <span className="struggled-name">{topic.topic_name}</span>
      {renderBar(topic, card === 'open')}
      {card !== 'closed' && (
        <div
          id={cardId}
          role="tooltip"
          className={`focus-pop ${card === 'closing' ? 'is-closing' : ''}`}
          onAnimationEnd={() => setCard((c) => (c === 'closing' ? 'closed' : c))}
        >
          {detail}
        </div>
      )}
    </li>
  );
}

// One of the overview's focus columns: a heading, the question it
// answers for the teacher, and its topics (or an empty-state line).
function FocusColumn({ title, purpose, items, emptyText, renderBar, renderDetail }) {
  return (
    <section className="teacher-card static focus-col" aria-label={title}>
      <h2 className="teacher-card-title">{title}</h2>
      <p className="focus-purpose">{purpose}</p>
      {items.length === 0 ? (
        <p className="teacher-card-stat">{emptyText}</p>
      ) : (
        <ul className="focus-list">
          {items.map((t) => (
            <FocusItem key={t.topic_id} topic={t} renderBar={renderBar} detail={renderDetail(t)} />
          ))}
        </ul>
      )}
    </section>
  );
}

function FocusColumns({ focus }) {
  const { newly_taught, weak_spots, windows } = focus;
  return (
    <>
      <BandLegend />
      <div className="focus-cols">
        <FocusColumn
          title="Newly taught"
          purpose="Familiarity with new topics"
          items={newly_taught}
          emptyText={`No assignments added new topics in the last ${windows.new_days} days.`}
          renderBar={(t, open) => <BandBar counts={t.proficiency} showPercents={open} />}
          renderDetail={(t) => (
            <>
              <span className="focus-pop-line">First assigned {fmtDate(t.first_assigned)}</span>
              <span className="focus-pop-line">
                {t.accuracy == null ? 'Not practiced yet' : `Average accuracy ${t.accuracy}%`}
              </span>
            </>
          )}
        />
        <FocusColumn
          title="Weak spots"
          purpose="Bars show average accuracy"
          items={weak_spots}
          emptyText="No missed answers yet."
          renderBar={(t, open) => <AccuracyBar accuracy={t.accuracy} showPercent={open} />}
          renderDetail={(t) => (
            <span className="focus-pop-line">
              {plural(t.missed_recent, 'student')} answered incorrectly in {pastDays(windows.missed_days)}
            </span>
          )}
        />
      </div>
    </>
  );
}

function TeacherOverview({ onOpenClass }) {
  // "" = all students across every class; otherwise a specific class id.
  const [scopeClass, setScopeClass] = useState('');

  const { data, isPending, error } = useQuery({
    queryKey: ['teacher', 'overview'],
    queryFn: async () => {
      const res = await apiFetch('/teacher/overview/');
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
  });

  const focus = useQuery({
    queryKey: ['teacher', 'overview', 'focus', scopeClass],
    queryFn: async () => {
      const params = new URLSearchParams({ today: localDay() });
      if (scopeClass) {
        params.set('scope', 'class');
        params.set('class_id', scopeClass);
      }
      const res = await apiFetch(`/teacher/overview/focus/?${params}`);
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
  });

  const selected = data?.classes.find((c) => String(c.id) === scopeClass);

  return (
    <div className="teacher-page">
      <h1>Overview</h1>
      {isPending && <p>Loading…</p>}
      {error && <p className="teacher-error">Failed to load overview.</p>}
      {data && (
        <>
          <p className="teacher-card-stat">
            {plural(data.total_students, 'student')} across your classes
          </p>

          {/* One dropdown scopes the focus columns and the trend chart alike. */}
          {data.classes.length > 0 && (
            <div className="teacher-field" style={{ maxWidth: '260px' }}>
              <label htmlFor="overview-class">Show</label>
              <select
                id="overview-class"
                value={scopeClass}
                onChange={(e) => setScopeClass(e.target.value)}
              >
                <option value="">All classes</option>
                {data.classes.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
          )}

          {focus.isPending && <p>Loading…</p>}
          {focus.error && <p className="teacher-error">Failed to load class focus.</p>}
          {focus.data && <FocusColumns focus={focus.data} />}

          <ProficiencyTrend
            title={selected ? `Familiarity over time — ${selected.name}` : 'Familiarity over time — all students'}
            description={
              selected
                ? "Topics in each proficiency band, by this class's average familiarity with each topic."
                : 'Topics in each proficiency band, by the average familiarity of every student in your classes.'
            }
            scope={selected ? 'class' : 'all'}
            classId={selected ? selected.id : undefined}
            defaultDays={30}
          />

          {data.classes.length === 0 ? (
            <p className="teacher-empty">You haven't created any classes yet.</p>
          ) : (
            <div className="teacher-cards">
              {data.classes.map((c) => (
                <button key={c.id} className="teacher-card" onClick={() => onOpenClass(c.id)}>
                  <div className="teacher-card-title">{c.name}</div>
                  <div className="teacher-card-stat">{c.student_count} students</div>
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
