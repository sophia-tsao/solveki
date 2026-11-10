import '../Teacher.css';

// Assignment states, each with an icon and a label so status never rides on
// color alone. Keys match the API's status values plus the derived flags.
export const STATUS = {
  done: { icon: '✓', label: 'Done' },
  in_progress: { icon: '◐', label: 'In progress' },
  not_started: { icon: '○', label: 'Not started' },
  overdue: { icon: '!', label: 'Overdue' },
  late: { icon: '!', label: 'Late' },
  needs_help: { icon: '⚑', label: 'Needs help' },
};

export const NEEDS_HELP_HINT =
  'Finished at the most cards this assignment gives, without getting solid on every topic';

// One status chip. `label` overrides the default wording (e.g. "3 not started").
export function StatusChip({ status, label, title }) {
  const s = STATUS[status];
  if (!s) return null;
  return (
    <span className={`status-chip ${status}`} title={title}>
      <span aria-hidden="true">{s.icon}</span>
      {label ?? s.label}
    </span>
  );
}

// A student's state on one assignment as chips: the main status, plus
// overdue / late / needs-help flags when they apply.
export function AssignmentStatusChips({ row }) {
  const status = row.overdue ? 'overdue' : row.status;
  return (
    <span className="status-chips">
      <StatusChip status={status} />
      {row.late && row.status === 'done' && <StatusChip status="late" />}
      {row.max_reached && <StatusChip status="needs_help" title={NEEDS_HELP_HINT} />}
    </span>
  );
}
