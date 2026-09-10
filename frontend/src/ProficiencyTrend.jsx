import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiFetch, localDay } from './auth.js';
import { LEVEL_COLOR } from './TopicProgress.jsx';
import './ProficiencyTrend.css';

// The four proficiency bands, in progression order, each mapped to the shared
// proficiency palette so the trend lines read as the same system as the
// dashboard donut and status dots. `young`/`mature` are the palette's internal
// keys for Familiar/Proficient.
const BANDS = [
  { key: 'new', label: 'New', color: LEVEL_COLOR.new },
  { key: 'learning', label: 'Learning', color: LEVEL_COLOR.learning },
  { key: 'familiar', label: 'Familiar', color: LEVEL_COLOR.young },
  { key: 'proficient', label: 'Proficient', color: LEVEL_COLOR.mature },
];

const VIEW_W = 640;
const VIEW_H = 300;
const MARGIN = { top: 16, right: 96, bottom: 36, left: 40 };
const PLOT_W = VIEW_W - MARGIN.left - MARGIN.right;
const PLOT_H = VIEW_H - MARGIN.top - MARGIN.bottom;

const yScale = (pct) => MARGIN.top + (1 - pct / 100) * PLOT_H;
const xScale = (i, n) => MARGIN.left + (n <= 1 ? PLOT_W / 2 : (i / (n - 1)) * PLOT_W);

function fmtDate(iso) {
  return new Date(`${iso}T00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
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
 * A familiarity-over-time line chart: one line per proficiency band showing the
 * percentage of a group's topics in that band, day by day. Used on the teacher
 * overview (all students / per class) and on a single student's page.
 */
function ProficiencyTrend({ title, description, scope = 'all', classId, studentId, days = 90 }) {
  const [hover, setHover] = useState(null); // index into series, or null
  const { data, isPending, error } = useHistory({ scope, classId, studentId, days });

  const series = data?.series || [];
  const n = series.length;

  function onMove(e) {
    if (n === 0) return;
    const svg = e.currentTarget.ownerSVGElement || e.currentTarget;
    const rect = svg.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * VIEW_W;
    const frac = (x - MARGIN.left) / PLOT_W;
    const i = Math.max(0, Math.min(n - 1, Math.round(frac * (n - 1))));
    setHover(i);
  }

  const yTicks = [0, 25, 50, 75, 100];
  const xTickIdx = n <= 1 ? [0] : [0, Math.floor((n - 1) / 2), n - 1];
  const point = hover != null ? series[hover] : null;

  return (
    <figure className="ptrend">
      <figcaption className="ptrend-head">
        <span className="ptrend-title">{title}</span>
        {description && <span className="ptrend-desc">{description}</span>}
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
            aria-label={`${title}: percentage of topics in each proficiency band over time`}
            onMouseMove={onMove}
            onMouseLeave={() => setHover(null)}
          >
            {/* Y gridlines + labels */}
            {yTicks.map((t) => (
              <g key={t}>
                <line x1={MARGIN.left} x2={VIEW_W - MARGIN.right} y1={yScale(t)} y2={yScale(t)} className="ptrend-grid" />
                <text x={MARGIN.left - 8} y={yScale(t) + 4} className="ptrend-axis ptrend-axis-y">{t}%</text>
              </g>
            ))}

            {/* X date labels */}
            {xTickIdx.map((i) => (
              <text key={i} x={xScale(i, n)} y={VIEW_H - 12} className="ptrend-axis ptrend-axis-x">
                {fmtDate(series[i].date)}
              </text>
            ))}

            {/* One line per band, with a direct label at its right end. */}
            {BANDS.map((b) => {
              const pts = series.map((d, i) => `${xScale(i, n).toFixed(1)},${yScale(d[b.key]).toFixed(1)}`).join(' ');
              const last = series[n - 1];
              return (
                <g key={b.key}>
                  {n === 1 ? (
                    <circle cx={xScale(0, n)} cy={yScale(last[b.key])} r="4" fill={b.color} />
                  ) : (
                    <polyline points={pts} fill="none" stroke={b.color} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
                  )}
                  <text
                    x={VIEW_W - MARGIN.right + 6}
                    y={yScale(last[b.key]) + 4}
                    className="ptrend-line-label"
                    style={{ fill: b.color }}
                  >
                    {b.label}
                  </text>
                </g>
              );
            })}

            {/* Hover crosshair + markers */}
            {point && (
              <g className="ptrend-hover">
                <line x1={xScale(hover, n)} x2={xScale(hover, n)} y1={MARGIN.top} y2={MARGIN.top + PLOT_H} className="ptrend-crosshair" />
                {BANDS.map((b) => (
                  <circle key={b.key} cx={xScale(hover, n)} cy={yScale(point[b.key])} r="3.5" fill={b.color} stroke="#fff" strokeWidth="1.5" />
                ))}
              </g>
            )}
          </svg>

          {point && (
            <div className="ptrend-tooltip" style={{ left: `${(xScale(hover, n) / VIEW_W) * 100}%` }}>
              <div className="ptrend-tooltip-date">{fmtDate(point.date)}</div>
              {BANDS.map((b) => (
                <div key={b.key} className="ptrend-tooltip-row">
                  <span className="ptrend-swatch" style={{ background: b.color }} />
                  <span className="ptrend-tooltip-label">{b.label}</span>
                  <span className="ptrend-tooltip-val">{point[b.key]}%</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {n > 0 && (
        <details className="ptrend-table-toggle">
          <summary>Show data table</summary>
          <table className="ptrend-table">
            <thead>
              <tr>
                <th>Date</th>
                {BANDS.map((b) => <th key={b.key}>{b.label}</th>)}
              </tr>
            </thead>
            <tbody>
              {series.map((d) => (
                <tr key={d.date}>
                  <td>{fmtDate(d.date)}</td>
                  {BANDS.map((b) => <td key={b.key}>{d[b.key]}%</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </details>
      )}
    </figure>
  );
}

export default ProficiencyTrend;
