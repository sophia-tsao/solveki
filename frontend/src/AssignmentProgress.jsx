// A student's progress on one assignment, for the teacher views: the
// completion percentage, plus flags for finishing only at the most cards the
// assignment can ask for ("needs help"), finishing after the due date, and
// being past due without finishing.
function AssignmentProgress({ row }) {
  const pct = row.status === 'done' ? 100 : (row.completion_pct ?? 0);
  return (
    <span>
      {pct}%
      {row.max_reached && (
        <span
          className="teacher-needs-help"
          title="Finished at the most cards this assignment gives, without getting solid on every topic"
        >
          {' '}· needs help
        </span>
      )}
      {row.late && <span className="teacher-overdue"> · late</span>}
      {row.overdue && <span className="teacher-overdue"> · overdue</span>}
    </span>
  );
}

export default AssignmentProgress;
