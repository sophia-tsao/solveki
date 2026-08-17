import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import './Dashboard.css';
import Calendar from './Calendar.jsx';
import { apiFetch, localDay } from './auth.js';
import { createLogger } from './logger.js';

const log = createLogger('dashboard');

async function fetchDashboard() {
  const response = await apiFetch(`/dashboard/?today=${localDay()}`);
  if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
  const result = await response.json();
  log.debug(`Loaded ${result.selected.length} selected, ${result.upcoming.length} upcoming`);
  return result;
}

// Bucket a topic's interval (days until next review) into a proficiency level.
// Short intervals mean the topic is still being learned / seen often; long
// intervals mean it's well-retained and rests longer between reviews. The four
// levels drive the deck grouping, the pie chart, and each card's status dot —
// one consistent color system across the whole dashboard.
function intervalLevel(interval) {
  if (interval <= 1) return 'new';
  if (interval < 6) return 'learning';
  if (interval < 21) return 'young';
  return 'mature';
}

// Ease is the SM-2 multiplier (floor 1.3, starts 2.5). Lower ease means the
// topic keeps coming up hard, so its intervals grow slowly — worth flagging.
function easeLevel(ease) {
  if (ease < 1.6) return 'new';
  if (ease < 2.2) return 'learning';
  if (ease < 2.6) return 'young';
  return 'mature';
}

// The four proficiency decks, in progression order. `level` keys the shared
// status colors (see .dash-dot-* in the CSS); `label` is the user-facing name.
const CATEGORIES = [
  { level: 'new', label: 'New', hint: 'Just started — seen almost every day.' },
  { level: 'learning', label: 'Learning', hint: 'Coming back within a few days.' },
  { level: 'young', label: 'Familiar', hint: 'Settling in — a week or two between reviews.' },
  { level: 'mature', label: 'Proficient', hint: 'Well retained — long gaps between reviews.' },
];

// Shared with the CSS .dash-dot-* classes so the pie, dots, and deck accents
// all read as the same system.
const LEVEL_COLOR = {
  new: '#ef4444',
  learning: '#f59e0b',
  young: '#3b82f6',
  mature: '#22c55e',
};

const MAX_PREVIEW = 4;

function Stat({ label, value, level }) {
  return (
    <div className="dash-stat">
      <span className="dash-stat-label">{label}</span>
      <span className="dash-stat-value">
        <span className={`dash-dot dash-dot-${level}`} />
        {value}
      </span>
    </div>
  );
}

function TopicCard({ topic }) {
  const level = intervalLevel(topic.interval);
  return (
    <div className="dash-card" data-level={level}>
      <div className="dash-card-head">
        <span className="dash-card-name">{topic.topic_name}</span>
        {topic.course_name && (
          <span className="dash-card-course">{topic.course_name}</span>
        )}
      </div>
      <div className="dash-card-stats-wrap">
        <div className="dash-card-stats">
          <Stat
            label="Repetitions"
            value={topic.repetitions}
            level={intervalLevel(topic.interval)}
          />
          <Stat
            label="Ease"
            value={topic.ease.toFixed(2)}
            level={easeLevel(topic.ease)}
          />
          <Stat
            label="Interval"
            value={topic.interval === 1 ? '1 day' : `${topic.interval} days`}
            level={intervalLevel(topic.interval)}
          />
        </div>
      </div>
    </div>
  );
}

// A deck: a titled panel showing up to MAX_PREVIEW topic cards, expandable to
// the full set. `level` (optional) colors the accent stripe and dot to match
// the proficiency system; "Shown soon" passes none and uses a neutral accent.
function Deck({ title, hint, level, topics }) {
  const [expanded, setExpanded] = useState(false);
  const overflow = topics.length - MAX_PREVIEW;
  const visible = expanded ? topics : topics.slice(0, MAX_PREVIEW);

  return (
    <section className="deck" data-level={level || 'soon'}>
      <header className="deck-head">
        <span className={`dash-dot dash-dot-${level || 'soon'}`} />
        <h2 className="deck-title">{title}</h2>
        <span className="deck-count">{topics.length}</span>
      </header>
      {hint && <p className="deck-hint">{hint}</p>}
      {topics.length === 0 ? (
        <p className="dash-empty">No topics here yet.</p>
      ) : (
        <>
          <div className="dash-cards">
            {visible.map((t) => <TopicCard key={t.id} topic={t} />)}
          </div>
          {overflow > 0 && (
            <button
              type="button"
              className="deck-toggle"
              aria-expanded={expanded}
              onClick={() => setExpanded((v) => !v)}
            >
              {expanded ? 'Show less' : `Show ${overflow} more`}
            </button>
          )}
        </>
      )}
    </section>
  );
}

// Compute the path for one pie wedge between two angles (degrees, clockwise
// from 12 o'clock): from the center out to the arc and back.
function pieSlice(cx, cy, r, startAngle, endAngle) {
  const toXY = (angle) => {
    const a = ((angle - 90) * Math.PI) / 180;
    return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
  };
  const [x1, y1] = toXY(startAngle);
  const [x2, y2] = toXY(endAngle);
  const large = endAngle - startAngle > 180 ? 1 : 0;
  return `M${cx} ${cy} L${x1} ${y1} A${r} ${r} 0 ${large} 1 ${x2} ${y2} Z`;
}

// Donut chart of the proficiency mix. Counts come in already grouped; the
// legend beside it carries the label + count, so identity is never color-only
// (the segment fills are below the WCAG 3:1 surface-contrast floor on their
// own — the legend text is the required relief).
function ProficiencyPie({ counts, total }) {
  const size = 360;
  const cx = size / 2;
  const cy = size / 2;
  const r = 156;
  // The reveal mask is a circle stroked so wide it fills the whole disc: a ring
  // at radius r/2 with stroke-width r spans from the center (0) out to r.
  const sweepR = r / 2;
  const circ = 2 * Math.PI * sweepR;
  const present = CATEGORIES.filter((c) => counts[c.level] > 0);

  let angle = 0;
  const segments = present.map((c) => {
    const sweep = (counts[c.level] / total) * 360;
    const seg = { level: c.level, start: angle, end: angle + sweep };
    angle += sweep;
    return seg;
  });

  return (
    <div className="dash-overview">
      <div className="dash-pie" role="img" aria-label="Topic proficiency mix">
        <svg
          viewBox={`0 0 ${size} ${size}`}
          width={size}
          height={size}
          preserveAspectRatio="xMidYMid meet"
        >
          <defs>
            {/* Clockwise "draw-on" reveal: a white disc in the mask grows from
                12 o'clock around, un-hiding the colored wedges beneath it. */}
            <mask id="dash-pie-reveal">
              <circle
                className="dash-pie-sweep"
                cx={cx}
                cy={cy}
                r={sweepR}
                fill="none"
                stroke="#ffffff"
                strokeWidth={r}
                transform={`rotate(-90 ${cx} ${cy})`}
                style={{ '--circ': circ }}
              />
            </mask>
          </defs>
          <g mask="url(#dash-pie-reveal)">
            {total === 0 ? (
              <circle cx={cx} cy={cy} r={r} fill="#e5e7eb" />
            ) : segments.length === 1 ? (
              // A single 100% category: a full disc (a 360° arc path is degenerate).
              <circle cx={cx} cy={cy} r={r} fill={LEVEL_COLOR[segments[0].level]} />
            ) : (
              segments.map((s) => (
                <path
                  key={s.level}
                  d={pieSlice(cx, cy, r, s.start, s.end)}
                  fill={LEVEL_COLOR[s.level]}
                  stroke="#ffffff"
                  strokeWidth="2"
                />
              ))
            )}
          </g>
        </svg>
      </div>
      <div className="dash-legend-wrap">
        <div className="dash-legend-total">
          <span className="dash-legend-total-num">{total}</span>
          <span className="dash-legend-total-label">
            {total === 1 ? 'topic selected' : 'topics selected'}
          </span>
        </div>
        <ul className="dash-legend">
          {CATEGORIES.map((c) => {
            const n = counts[c.level] || 0;
            const pct = total ? Math.round((n / total) * 100) : 0;
            return (
              <li key={c.level} className="dash-legend-row">
                <span className={`dash-dot dash-dot-${c.level}`} />
                <span className="dash-legend-label">{c.label}</span>
                <span className="dash-legend-count">{n}</span>
                <span className="dash-legend-pct">{pct}%</span>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

function Dashboard() {
  const { data, error } = useQuery({
    queryKey: ['dashboard', localDay()],
    queryFn: fetchDashboard,
  });
  const selected = data?.selected ?? [];
  const upcoming = data?.upcoming ?? [];

  // Group the selected topics into the four proficiency decks.
  const byLevel = { new: [], learning: [], young: [], mature: [] };
  for (const t of selected) byLevel[intervalLevel(t.interval)].push(t);
  const counts = {
    new: byLevel.new.length,
    learning: byLevel.learning.length,
    young: byLevel.young.length,
    mature: byLevel.mature.length,
  };

  return (
    <div className="dashboard">
      <header className="dash-intro">
        <h1 className="dash-title">Your progress</h1>
        <p className="dash-subtitle">
          A snapshot of everything you're reviewing — each topic grouped by how
          well you know it, plus your overall mix and practice history.
        </p>
      </header>

      {error && <p className="dash-error">Error: {error.message}</p>}

      <section className="dash-section dash-section-widgets">
        <div className="dash-section-head">
          <h2 className="dash-section-title">Overview &amp; practice history</h2>
          <p className="dash-section-desc">
            Your proficiency mix at a glance, and the days you've practiced this
            month.
          </p>
        </div>
        <div className="dash-widgets">
          <ProficiencyPie counts={counts} total={selected.length} />
          <Calendar />
        </div>
      </section>

      <section className="dash-section dash-section-decks">
        <div className="dash-section-head">
          <h2 className="dash-section-title">Topics by proficiency</h2>
          <p className="dash-section-desc">
            Every topic you've selected, grouped by how well you've learned it.
            Hover a card to see its review stats.
          </p>
        </div>
        <div className="dash-decks">
          {CATEGORIES.map((c) => (
            <Deck
              key={c.level}
              title={c.label}
              hint={c.hint}
              level={c.level}
              topics={byLevel[c.level]}
            />
          ))}
          <Deck
            title="Shown soon"
            hint="The topics your next practice session will draw from."
            topics={upcoming}
          />
        </div>
      </section>
    </div>
  );
}

export default Dashboard;
