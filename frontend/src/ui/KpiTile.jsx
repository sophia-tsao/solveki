import '../Teacher.css';

// One headline number: a label, the value (with an optional "/ total"), and a
// note line underneath for context or the change since last period.
function KpiTile({ label, value, total, note, tone, children }) {
  return (
    <div className="kpi-tile">
      <div className="kpi-label">{label}</div>
      <div className={`kpi-value${tone ? ` ${tone}` : ''}`}>
        {value}
        {total != null && <small>/ {total}</small>}
      </div>
      {note && <div className="kpi-note">{note}</div>}
      {children}
    </div>
  );
}

// "▲ 3 vs last week" / "▼ 4 pts vs last week", or nothing when there's no
// comparison. `unit` follows the number (e.g. " pts").
export function Delta({ value, unit = '', suffix = 'vs last week' }) {
  if (value == null || value === 0) return suffix ? <span>No change {suffix}</span> : null;
  const up = value > 0;
  return (
    <span>
      <span className={up ? 'kpi-up' : 'kpi-down'}>
        {up ? '▲' : '▼'} {Math.abs(value)}{unit}
      </span>{' '}
      {suffix}
    </span>
  );
}

export default KpiTile;
