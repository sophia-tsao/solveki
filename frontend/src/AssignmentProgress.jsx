import { StatusChip, NEEDS_HELP_HINT } from './ui/StatusChip.jsx';

// A student's progress on one assignment, for the teacher views: a completion
// bar and percentage. With `flags`, chips follow for finishing only at the most
// cards the assignment can ask for ("needs help"), finishing after the due
// date, and being past due without finishing.
function AssignmentProgress({ row, flags = false }) {
  const done = row.status === 'done';
  const pct = done ? 100 : (row.completion_pct ?? 0);
  const tone = row.max_reached ? 'needs_help' : done ? 'done' : '';
  return (
    <span className="teacher-progress">
      <span className="teacher-progress-track" aria-hidden="true">
        <span className={`teacher-progress-fill ${tone}`} style={{ width: `${pct}%` }} />
      </span>
      <span className="teacher-progress-label">{pct}%</span>
      {flags && (
        <span className="status-chips">
          {row.max_reached && <StatusChip status="needs_help" title={NEEDS_HELP_HINT} />}
          {row.late && <StatusChip status="late" />}
          {row.overdue && <StatusChip status="overdue" />}
        </span>
      )}
    </span>
  );
}

export default AssignmentProgress;
