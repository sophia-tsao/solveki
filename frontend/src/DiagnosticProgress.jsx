// A determinate progress bar for the diagnostic test. The total step count is
// known up front (profile questions + capped calibration problems), so the bar
// always reflects a real fraction — the user can see how close they are to done.
function DiagnosticProgress({ completed, total }) {
  const safeTotal = total > 0 ? total : 1;
  const done = Math.min(completed, safeTotal);
  const percent = Math.round((done / safeTotal) * 100);
  const label = done >= safeTotal
    ? 'All done!'
    : `Step ${done + 1} of ${safeTotal}`;
  return (
    <div className="diagnostic-progress">
      <div
        className="diagnostic-progress-track"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={safeTotal}
        aria-valuenow={done}
        aria-label="Diagnostic progress"
      >
        <div className="diagnostic-progress-fill" style={{ width: `${percent}%` }} />
      </div>
      <span className="diagnostic-progress-label">{label}</span>
    </div>
  );
}

export default DiagnosticProgress;
