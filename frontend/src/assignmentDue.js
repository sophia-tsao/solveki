// An assignment's due date as shown to students ("No due date" when it has none).
export function formatDue(due) {
  if (!due) return 'No due date';
  return `Due ${new Date(due).toLocaleString()}`;
}
