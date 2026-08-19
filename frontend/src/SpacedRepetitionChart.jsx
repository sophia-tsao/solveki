// An explanatory (not data-driven) diagram of how spaced repetition keeps a
// memory alive. It contrasts two curves over the same span of time:
//   - "Without review": a single forgetting curve that decays toward zero.
//   - "With Solveki": a sawtooth where each review resets retention to full and
//     the following decay is slower, so the gaps between reviews can grow.
// Rendered as inline SVG so it needs no charting dependency.

const VIEW_W = 640;
const VIEW_H = 340;
const MARGIN = { top: 24, right: 24, bottom: 44, left: 52 };
const PLOT_W = VIEW_W - MARGIN.left - MARGIN.right;
const PLOT_H = VIEW_H - MARGIN.top - MARGIN.bottom;
const DAYS = 30;

// Colors live in LoginPage.css: brand blue #2563eb for the "with review" story,
// amber #d97706 for the forgetting curve. That pair validates as colorblind-safe,
// and each curve is also distinguished by dash style and a direct label.
const xScale = (t) => MARGIN.left + (t / DAYS) * PLOT_W;
const yScale = (retention) => MARGIN.top + (1 - retention / 100) * PLOT_H;

// Build an SVG polyline "x,y x,y ..." string from time/retention samples.
function toPoints(samples) {
  return samples.map(([t, r]) => `${xScale(t).toFixed(1)},${yScale(r).toFixed(1)}`).join(' ');
}

// Exponential forgetting curve: retention falls off fast, then flattens.
function forgettingSamples() {
  const pts = [];
  for (let t = 0; t <= DAYS; t += 0.5) {
    pts.push([t, 100 * Math.exp(-t / 5)]);
  }
  return pts;
}

// Reviews happen at growing intervals. After each review the memory is more
// stable, so it decays to a higher floor before the next review is due.
const REVIEWS = [
  { start: 0, end: 3, floor: 66 },
  { start: 3, end: 8, floor: 73 },
  { start: 8, end: 16, floor: 80 },
  { start: 16, end: DAYS, floor: 86 },
];

// The sawtooth: within each interval retention decays exponentially from 100%
// down to that interval's floor, then jumps back to 100% at the next review.
function spacedSamples() {
  const pts = [];
  for (const { start, end, floor } of REVIEWS) {
    const span = end - start;
    const steps = 24;
    for (let i = 0; i <= steps; i += 1) {
      const t = start + (span * i) / steps;
      const frac = i / steps;
      pts.push([t, 100 * Math.pow(floor / 100, frac)]);
    }
    // Vertical jump back to full retention at the moment of review.
    if (end < DAYS) pts.push([end, 100]);
  }
  return pts;
}

// Points where a review resets the curve to 100% — marked with dots.
const REVIEW_MARKERS = REVIEWS.filter((r) => r.start > 0).map((r) => r.start);

function SpacedRepetitionChart() {
  const gridLines = [0, 50, 100];
  return (
    <figure className="sr-chart">
      <svg
        viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
        role="img"
        aria-labelledby="sr-chart-title sr-chart-desc"
        className="sr-chart-svg"
      >
        <title id="sr-chart-title">How spaced repetition protects memory</title>
        <desc id="sr-chart-desc">
          Two curves over 30 days. Without review, memory decays quickly toward
          zero. With Solveki, each review restores full retention and later
          reviews can be spaced further apart while memory stays high.
        </desc>

        {/* Horizontal gridlines + y-axis retention labels */}
        {gridLines.map((r) => (
          <g key={r}>
            <line
              x1={MARGIN.left}
              x2={VIEW_W - MARGIN.right}
              y1={yScale(r)}
              y2={yScale(r)}
              className="sr-grid"
            />
            <text x={MARGIN.left - 10} y={yScale(r) + 4} className="sr-axis-label sr-axis-label-y">
              {r}%
            </text>
          </g>
        ))}

        {/* Axis titles */}
        <text
          x={MARGIN.left}
          y={VIEW_H - 10}
          className="sr-axis-title"
        >
          Time (days) →
        </text>

        {/* Forgetting curve — no review */}
        <polyline points={toPoints(forgettingSamples())} className="sr-line sr-line-without" />

        {/* Spaced repetition curve — reviews reset retention to full */}
        <polyline points={toPoints(spacedSamples())} className="sr-line sr-line-with" />

        {/* Review markers */}
        {REVIEW_MARKERS.map((t) => (
          <circle key={t} cx={xScale(t)} cy={yScale(100)} r="4.5" className="sr-review-dot" />
        ))}
        <text x={xScale(8)} y={yScale(100) - 12} className="sr-review-label">
          reviews
        </text>

        {/* Direct labels on each curve (identity is never color alone) */}
        <text x={xScale(DAYS)} y={yScale(90) - 6} className="sr-curve-label sr-curve-label-with">
          With Solveki
        </text>
        <text x={xScale(DAYS)} y={yScale(14)} className="sr-curve-label sr-curve-label-without">
          Without review
        </text>
      </svg>
      <figcaption className="sr-chart-caption">
        Each review lands just before you would forget, resetting memory to full
        &mdash; and every time, the knowledge fades more slowly, so reviews grow
        further apart.
      </figcaption>
    </figure>
  );
}

export default SpacedRepetitionChart;
