import { useId, useState } from 'react';
import { BANDS } from './BandBar.jsx';
import { niceTicks } from './chartTicks.js';
import './AssignmentCharts.css';

const BAND = Object.fromEntries(BANDS.map((b) => [b.key, b]));
const DAY_MS = 24 * 60 * 60 * 1000;

// Dates are local calendar days as 'YYYY-MM-DD', which compare as strings.
const toDate = (iso) => new Date(`${iso}T00:00`);
const toIso = (d) => d.toLocaleDateString('en-CA');
const daysBetween = (a, b) => Math.round((toDate(b) - toDate(a)) / DAY_MS);
const addDays = (iso, n) => {
  const d = toDate(iso);
  d.setDate(d.getDate() + n);
  return toIso(d);
};

export function fmtDay(iso) {
  return toDate(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

/**
 * A student's familiarity band over time on an assignment's topics: one
 * segment per stretch they stayed in a band, so each boundary is a switch.
 * `range` is the span shared by every student's bar ({start, end}), so bars
 * line up; the part before the assignment reached the student stays empty.
 * Hovering shows the day under the pointer and the band held then.
 */
export function BandTimeline({ segments, range }) {
  const [hoverDay, setHoverDay] = useState(null);
  if (!segments?.length) return <span className="teacher-card-stat">—</span>;

  const total = daysBetween(range.start, range.end) + 1;
  const pct = (days) => (days / total) * 100;
  const label = segments
    .map((s) => `${BAND[s.band].label} ${fmtDay(s.start)}${s.end !== s.start ? `–${fmtDay(s.end)}` : ''}`)
    .join(', ');

  const onMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const frac = rect.width ? (e.clientX - rect.left) / rect.width : 0;
    const i = Math.min(total - 1, Math.max(0, Math.floor(frac * total)));
    setHoverDay(addDays(range.start, i));
  };
  const hoverSeg = hoverDay && segments.find((s) => s.start <= hoverDay && hoverDay <= s.end);

  return (
    <span className="tl" onMouseMove={onMove} onMouseLeave={() => setHoverDay(null)}>
      <span className="tl-track" role="img" aria-label={label}>
        {segments.map((s, i) => (
          <span
            key={s.start}
            className={`tl-seg${i > 0 ? ' is-switch' : ''}`}
            style={{
              left: `${pct(daysBetween(range.start, s.start))}%`,
              width: `${pct(daysBetween(s.start, s.end) + 1)}%`,
              background: BAND[s.band].color,
            }}
          />
        ))}
      </span>
      {hoverDay && (
        <>
          <span className="tl-cursor" style={{ left: `${pct(daysBetween(range.start, hoverDay) + 0.5)}%` }} />
          <span
            className="ad-tooltip tl-tooltip"
            role="tooltip"
            style={{ left: `${pct(daysBetween(range.start, hoverDay) + 0.5)}%` }}
          >
            <span className="ad-tooltip-title">{fmtDay(hoverDay)}</span>
            {hoverSeg ? (
              <span className="ad-tooltip-row">
                <span className="ad-swatch" style={{ background: BAND[hoverSeg.band].color }} />
                <span>{BAND[hoverSeg.band].label}</span>
                <span className="ad-tooltip-muted">since {fmtDay(hoverSeg.start)}</span>
              </span>
            ) : (
              <span className="ad-tooltip-row ad-tooltip-muted">Not assigned yet</span>
            )}
          </span>
        </>
      )}
    </span>
  );
}

/**
 * Familiarity by topic: pick a topic, and one bar per band shows how many
 * assigned students sit in it. The axis runs to the topic's student count, so
 * switching topics keeps the same scale. Hovering a bar shows its share.
 */
export function TopicBandChart({ topics }) {
  const [picked, setPicked] = useState(null); // topic_id, or null for the first
  const [hover, setHover] = useState(null); // band key, or null
  const pickerId = useId();
  // The class filter can drop the picked topic; fall back to the first.
  const topic = topics.find((t) => t.topic_id === picked) || topics[0];
  const count = (b) => topic.proficiency[b.key] || 0;
  const total = BANDS.reduce((sum, b) => sum + count(b), 0);
  const ticks = niceTicks(total);
  const yMax = ticks[ticks.length - 1];
  const y = (v) => `${(v / yMax) * 100}%`;
  const share = (n) => (total ? Math.round((n / total) * 100) : 0);
  const columns = { gridTemplateColumns: `repeat(${BANDS.length}, minmax(0, 1fr))` };

  return (
    <figure className="tbc">
      <div className="teacher-field tbc-picker">
        <label htmlFor={pickerId}>Topic</label>
        <select id={pickerId} value={topic.topic_id} onChange={(e) => setPicked(Number(e.target.value))}>
          {topics.map((t) => <option key={t.topic_id} value={t.topic_id}>{t.topic_name}</option>)}
        </select>
      </div>
      <div className="tbc-axis-title" aria-hidden="true">Students</div>

      <div className="tbc-chart">
        <div className="tbc-yaxis" aria-hidden="true">
          {ticks.map((t) => <span key={t} style={{ bottom: y(t) }}>{t}</span>)}
        </div>

        <div className="tbc-main">
          <div className="tbc-plot" style={columns} onMouseLeave={() => setHover(null)}>
            <div className="tbc-grid" aria-hidden="true">
              {ticks.map((t) => <span key={t} className="tbc-gridline" style={{ bottom: y(t) }} />)}
            </div>

            {BANDS.map((b) => {
              const n = count(b);
              const dimmed = hover != null && hover !== b.key;
              return (
                <div
                  key={b.key}
                  className={`tbc-col${dimmed ? ' is-dimmed' : ''}`}
                  onMouseEnter={() => setHover(b.key)}
                >
                  <span className="tbc-bar-wrap" style={{ height: y(n) }}>
                    <span className="tbc-value" aria-hidden="true">{n}</span>
                    <span
                      className="tbc-bar"
                      role="img"
                      aria-label={`${topic.topic_name}, ${b.label}: ${n} student${n === 1 ? '' : 's'}`}
                      style={{ background: b.color }}
                    />
                  </span>
                  {hover === b.key && (
                    <span className="ad-tooltip tbc-tooltip" role="tooltip" style={{ bottom: `calc(${y(n)} + 1.5rem)` }}>
                      <span className="ad-tooltip-title">{b.label}</span>
                      <span className="ad-tooltip-row">
                        <span>{n} of {total} student{total === 1 ? '' : 's'}</span>
                        <span className="ad-tooltip-val">{share(n)}%</span>
                      </span>
                    </span>
                  )}
                </div>
              );
            })}
          </div>

          <div className="tbc-xlabels" style={columns} aria-hidden="true">
            {BANDS.map((b) => <span key={b.key} className="tbc-label">{b.label}</span>)}
          </div>
        </div>
      </div>
    </figure>
  );
}
