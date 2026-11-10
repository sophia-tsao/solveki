import { STATUS } from './StatusChip.jsx';
import '../Teacher.css';

// Counted, clickable status buckets above a student table. `counts` maps a
// bucket key to its count; `value` is the active filter (null = all) and
// clicking the active bucket again clears it.
export const COUNTER_KEYS = ['done', 'in_progress', 'not_started', 'overdue', 'needs_help'];

function StatusCounters({ total, counts, value, onChange }) {
  return (
    <div className="status-counters" role="group" aria-label="Filter by status">
      <button
        type="button"
        className="status-counter"
        aria-pressed={value == null}
        onClick={() => onChange(null)}
      >
        <span className="status-counter-label">Assigned</span>
        <span className="status-counter-value">{total}</span>
      </button>
      {COUNTER_KEYS.map((key) => (
        <button
          key={key}
          type="button"
          className={`status-counter ${key}`}
          aria-pressed={value === key}
          onClick={() => onChange(value === key ? null : key)}
        >
          <span className="status-counter-label">
            <span aria-hidden="true">{STATUS[key].icon}</span> {STATUS[key].label}
          </span>
          <span className="status-counter-value">{counts[key] || 0}</span>
        </button>
      ))}
    </div>
  );
}

export default StatusCounters;
