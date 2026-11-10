import { useId, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiFetch, localDay } from './auth.js';
import { LEVEL_COLOR } from './TopicProgress.jsx';
import { niceTicks } from './chartTicks.js';
import './Teacher.css';
import './ProficiencyTrend.css';

// The four proficiency bands, in progression order, each mapped to the shared
// proficiency palette so the bars read as the same system as the dashboard
// donut and status dots. `young`/`mature` are the palette's internal keys for
// Familiar/Proficient. Stacked from the baseline up in this order.
const BANDS = [
  { key: 'new', label: 'New', color: LEVEL_COLOR.new },
  { key: 'learning', label: 'Learning', color: LEVEL_COLOR.learning },
  { key: 'familiar', label: 'Familiar', color: LEVEL_COLOR.young },
  { key: 'proficient', label: 'Proficient', color: LEVEL_COLOR.mature },
];

// Time frames the viewer can switch between, in days of history.
export const RANGES = [
  { days: 7, label: 'Past week' },
  { days: 30, label: 'Past month' },
  { days: 90, label: 'Past 3 months' },
  { days: 365, label: 'Past year' },
];

// Past this many days, show one bar per week (its last day) so bars stay readable.
const MAX_DAILY_BARS = 90;

const VIEW_W = 640;
const VIEW_H = 300;
const MARGIN = { top: 24, right: 16, bottom: 36, left: 40 };
const PLOT_H = VIEW_H - MARGIN.top - MARGIN.bottom;
const BASELINE = MARGIN.top + PLOT_H;
const MAX_BAR_W = 24;
const SEG_GAP = 2; // surface gap between stacked segments
const CAP_R = 4; // rounded data-end on the top segment

function fmtDate(iso) {
  return new Date(`${iso}T00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

const total = (d) => BANDS.reduce((sum, b) => sum + d[b.key], 0);

// A rect whose top corners are rounded by `r` and bottom stays square.
function topRoundedRect(x, y, w, h, r) {
  const rr = Math.min(r, w / 2, h);
  return `M${x},${y + h}V${y + rr}Q${x},${y} ${x + rr},${y}H${x + w - rr}Q${x + w},${y} ${x + w},${y + rr}V${y + h}Z`;
}

function useHistory({ scope, classId, studentId, days }) {
  const params = new URLSearchParams({ scope, days: String(days), today: localDay() });
  if (scope === 'class' && classId != null) params.set('class_id', String(classId));
  if (scope === 'student' && studentId != null) params.set('student_id', String(studentId));
  const qs = params.toString();
  return useQuery({
    queryKey: ['proficiency-history', scope, classId ?? null, studentId ?? null, days],
    queryFn: async () => {
      const res = await apiFetch(`/teacher/proficiency-history/?${qs}`);
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
  });
}

/**
 * A familiarity-over-time stacked bar chart: one bar per day, split into the
 * number of topics in each proficiency band. For a group, each topic is banded
 * by the students' average familiarity with it, so bars grow as topics are
 * added. Used on the teacher overview (all students / per class) and on a
 * single student's page. `defaultDays` is the starting time frame, which the
 * viewer can switch. `sideControls` moves the time frame and legend into a
 * column flush against the plot's right edge (the student page).
 */
function ProficiencyTrend({
  title, description, scope = 'all', classId, studentId, defaultDays = 30, sideControls = false,
}) {
  const [hover, setHover] = useState(null); // index into bars, or null
  const [days, setDays] = useState(defaultDays);
  const rangeId = useId();
  const { data, isPending, error } = useHistory({ scope, classId, studentId, days });

  const series = data?.series || [];
  // Long ranges: keep each week's last day, counting back from the newest.
  const bars = series.length > MAX_DAILY_BARS
    ? series.filter((_, i) => (series.length - 1 - i) % 7 === 0)
    : series;
  const n = bars.length;

  const yTicks = niceTicks(Math.max(0, ...bars.map(total)));
  const yMax = yTicks[yTicks.length - 1];
  const yScale = (v) => BASELINE - (v / yMax) * PLOT_H;
  // With side controls the plot runs flush against the column to its right.
  const marginRight = sideControls ? 0 : MARGIN.right;
  const plotW = VIEW_W - MARGIN.left - marginRight;
  const slot = plotW / Math.max(n, 1);
  const barW = Math.max(1, Math.min(MAX_BAR_W, slot * 0.7));
  const barX = (i) => MARGIN.left + i * slot + (slot - barW) / 2;
  const xTickIdx = n <= 1 ? [0] : [0, Math.floor((n - 1) / 2), n - 1];
  const point = hover != null ? bars[hover] : null;

  const onRange = (e) => { setDays(Number(e.target.value)); setHover(null); };
  // The time frame picker, styled as a .teacher-field like the page's other filters.
  const rangeField = (
    <div className="teacher-field ptrend-range">
      <label htmlFor={rangeId}>Time frame</label>
      <select id={rangeId} value={days} onChange={onRange}>
        {RANGES.map((r) => <option key={r.days} value={r.days}>{r.label}</option>)}
      </select>
    </div>
  );

  const chart = (
    <>
      {isPending && <p className="ptrend-note">Loading…</p>}
      {error && <p className="ptrend-note ptrend-error">Failed to load progress.</p>}
      {!isPending && !error && n === 0 && (
        <p className="ptrend-note">No practice recorded yet — this fills in as students practice.</p>
      )}

      {n > 0 && (
        <div className="ptrend-plot-wrap">
          <svg
            viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
            className="ptrend-svg"
            role="img"
            aria-label={`${title}: number of topics in each proficiency band over time`}
            onMouseLeave={() => setHover(null)}
          >
            {/* Y axis title, gridlines + labels */}
            <text x={MARGIN.left - 8} y={MARGIN.top - 12} className="ptrend-axis ptrend-axis-title">
              Topics
            </text>
            {yTicks.map((t) => (
              <g key={t}>
                <line x1={MARGIN.left} x2={VIEW_W - marginRight} y1={yScale(t)} y2={yScale(t)} className="ptrend-grid" />
                <text x={MARGIN.left - 8} y={yScale(t) + 4} className="ptrend-axis ptrend-axis-y">{t}</text>
              </g>
            ))}

            {/* X date labels. With no right margin, the last one right-aligns to
                its bar so it isn't cut off at the edge. */}
            {xTickIdx.map((i) => {
              const flushEnd = sideControls && i > 0 && i === n - 1;
              return (
                <text
                  key={i}
                  x={flushEnd ? barX(i) + barW : barX(i) + barW / 2}
                  y={VIEW_H - 12}
                  className={`ptrend-axis ptrend-axis-x${flushEnd ? ' is-last' : ''}`}
                >
                  {fmtDate(bars[i].date)}
                </text>
              );
            })}

            {/* One stacked bar per day: bands from the baseline up, split by a
                surface gap, the top segment carrying the rounded data-end. */}
            {bars.map((d, i) => {
              const top = [...BANDS].reverse().find((b) => d[b.key] > 0)?.key;
              let y = BASELINE;
              return (
                <g key={d.date} className={hover != null && hover !== i ? 'ptrend-bar is-dimmed' : 'ptrend-bar'}>
                  {BANDS.map((b) => {
                    const h = (d[b.key] / yMax) * PLOT_H;
                    if (h <= 0) return null;
                    y -= h;
                    const gap = b.key === top || h <= SEG_GAP ? 0 : SEG_GAP;
                    const x = barX(i);
                    return b.key === top ? (
                      <path key={b.key} d={topRoundedRect(x, y, barW, h, CAP_R)} fill={b.color} />
                    ) : (
                      <rect key={b.key} x={x} y={y + gap} width={barW} height={h - gap} fill={b.color} />
                    );
                  })}
                </g>
              );
            })}

            {/* Hit targets: each bar's whole slot, taller than the bar itself. */}
            {bars.map((d, i) => (
              <rect
                key={d.date}
                x={MARGIN.left + i * slot}
                y={MARGIN.top}
                width={slot}
                height={PLOT_H}
                className="ptrend-hit"
                onMouseEnter={() => setHover(i)}
              />
            ))}
          </svg>

          {point && (
            <div className="ptrend-tooltip" style={{ left: `${((barX(hover) + barW / 2) / VIEW_W) * 100}%` }}>
              <div className="ptrend-tooltip-date">{fmtDate(point.date)}</div>
              {[...BANDS].reverse().map((b) => (
                <div key={b.key} className="ptrend-tooltip-row">
                  <span className="ptrend-swatch" style={{ background: b.color }} />
                  <span className="ptrend-tooltip-label">{b.label}</span>
                  <span className="ptrend-tooltip-val">{point[b.key]}</span>
                </div>
              ))}
              <div className="ptrend-tooltip-row ptrend-tooltip-total">
                <span className="ptrend-tooltip-label">Total</span>
                <span className="ptrend-tooltip-val">{total(point)}</span>
              </div>
            </div>
          )}
        </div>
      )}
    </>
  );

  if (sideControls) {
    return (
      <figure className="ptrend">
        <figcaption className="ptrend-head">
          <span className="ptrend-title">{title}</span>
          {description && <span className="ptrend-desc">{description}</span>}
        </figcaption>
        <div className="ptrend-body">
          <div className="ptrend-main">{chart}</div>
          {/* The time frame, then the legend (identity is never color alone),
              listed top-down in the bars' stacking order. */}
          <div className="ptrend-side">
            {rangeField}
            <ul className="ptrend-legend ptrend-side-legend">
              {[...BANDS].reverse().map((b) => (
                <li key={b.key} className="ptrend-legend-item">
                  <span className="ptrend-swatch" style={{ background: b.color }} />
                  {b.label}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </figure>
    );
  }

  return (
    <figure className="ptrend">
      <figcaption className="ptrend-head">
        <span className="ptrend-title">{title}</span>
        {description && <span className="ptrend-desc">{description}</span>}
        {rangeField}
      </figcaption>

      {/* Legend — identity is never color alone. */}
      <ul className="ptrend-legend">
        {BANDS.map((b) => (
          <li key={b.key} className="ptrend-legend-item">
            <span className="ptrend-swatch" style={{ background: b.color }} />
            {b.label}
          </li>
        ))}
      </ul>

      {chart}
    </figure>
  );
}

export default ProficiencyTrend;
