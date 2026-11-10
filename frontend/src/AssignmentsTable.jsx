import OverflowMenu from './ui/OverflowMenu.jsx';
import { StatusChip } from './ui/StatusChip.jsx';
import { useSortable } from './ui/useSortable.js';
import { fmtRelativeDue, fmtShortDate, plural } from './ui/format.js';
import './Teacher.css';

// Where an assignment stands for the list tabs: not assigned to any class yet,
// past due everywhere it's assigned, or open.
export function assignmentPhase(a, now = new Date()) {
  const classes = a.classes || [];
  if (classes.length === 0) return 'unassigned';
  const pastDue = classes.every((c) => c.due_at && new Date(c.due_at) < now);
  return pastDue ? 'past_due' : 'open';
}

function Completion({ counts }) {
  if (!counts || !counts.assigned) return <span className="teacher-muted">No students yet</span>;
  const pct = Math.round((counts.done / counts.assigned) * 100);
  return (
    <span className="teacher-progress">
      <span className="teacher-progress-track" aria-hidden="true">
        <span className="teacher-progress-fill" style={{ width: `${pct}%` }} />
      </span>
      <span className="teacher-progress-label">{counts.done}/{counts.assigned}</span>
    </span>
  );
}

// The flags worth a teacher's attention on a row, each spelled out.
function Flags({ counts }) {
  if (!counts) return null;
  const chips = [];
  if (counts.overdue) chips.push(<StatusChip key="o" status="overdue" label={`${counts.overdue} overdue`} />);
  if (counts.needs_help) {
    chips.push(<StatusChip key="h" status="needs_help" label={`${counts.needs_help} need${counts.needs_help === 1 ? 's' : ''} help`} />);
  }
  if (counts.not_started) {
    chips.push(<StatusChip key="n" status="not_started" label={`${counts.not_started} not started`} />);
  }
  return chips.length ? <span className="status-chips">{chips}</span> : <span className="teacher-muted">—</span>;
}

// A sortable table of assignments with their classes, due date, completion and
// flags. `showClasses` is off inside a class page. Row actions come from
// `actions(a)` (a list of { label, onSelect, danger? } for the ⋯ menu).
function AssignmentsTable({ assignments, today, showClasses = true, onOpen, actions }) {
  const { rows, headerProps, ariaSort } = useSortable(assignments, {
    title: (a) => a.title.toLowerCase(),
    due: (a) => a.next_due_at,
    done: (a) => (a.counts?.assigned ? a.counts.done / a.counts.assigned : null),
  });
  const th = (key, label, extra = {}) => (
    <th aria-sort={ariaSort(key)} {...extra}><button {...headerProps(key)}>{label}</button></th>
  );
  return (
    <div className="teacher-box teacher-scroll">
      <table className="teacher-table">
        <thead>
          <tr>
            {th('title', 'Assignment')}
            {showClasses && <th>Classes</th>}
            {th('due', 'Due')}
            {th('done', 'Completed', { style: { width: '20%' } })}
            <th>Flags</th>
            {actions && <th><span className="visually-hidden">Actions</span></th>}
          </tr>
        </thead>
        <tbody>
          {rows.map((a) => (
            <tr key={a.id} className="teacher-row-link" onClick={() => onOpen(a.id)}>
              <td>
                <button
                  type="button"
                  className="teacher-link"
                  onClick={(e) => { e.stopPropagation(); onOpen(a.id); }}
                >
                  {a.title}
                </button>
                <span className="row-sub">
                  {a.topic_count != null && `${plural(a.topic_count, 'topic')} · `}
                  {a.deck_size}–{a.max_cards ?? a.deck_size} cards
                  {a.allow_late === false && ' · no late work'}
                </span>
              </td>
              {showClasses && (
                <td>
                  {(a.classes || []).length === 0
                    ? <span className="teacher-muted">Not assigned</span>
                    : a.classes.map((c) => <span key={c.class_id} className="teacher-pill">{c.class_name}</span>)}
                </td>
              )}
              <td>
                {a.next_due_at ? (
                  <>
                    {fmtShortDate(a.next_due_at)}
                    <span className="row-sub">{fmtRelativeDue(a.next_due_at, today)}</span>
                  </>
                ) : <span className="teacher-muted">No due date</span>}
              </td>
              <td><Completion counts={a.counts} /></td>
              <td><Flags counts={a.counts} /></td>
              {actions && (
                <td className="num">
                  <OverflowMenu label={`Actions for ${a.title}`} items={actions(a)} />
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default AssignmentsTable;
