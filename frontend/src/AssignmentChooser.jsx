import { formatDue } from './assignmentDue.js';
import './Assignments.css';

// The practice page when several assignments are open: each has its own deck
// for the day, so the student picks which one to work on. `choices` come from
// the deck endpoint's `choose` payload, soonest due first.
function AssignmentChooser({ choices, onOpen }) {
  return (
    <div className="assignments-page">
      <h1>Choose an assignment</h1>
      <ul className="assignments-list">
        {choices.map((a) => (
          <li key={a.assignment_id} className="assignments-item">
            <div className="assignments-item-main">
              <span className="assignments-item-title">{a.title}</span>
              <span className="assignments-item-meta">
                {formatDue(a.due_at)}
                {` · ${a.completion_pct ?? 0}% done`}
              </span>
            </div>
            <button className="assignments-item-action" onClick={() => onOpen(a.assignment_id)}>
              {a.cards_answered > 0 ? 'Continue' : 'Begin'}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default AssignmentChooser;
