// Persist the diagnostic's status per user in localStorage so the Courses-page
// entry button can offer "Take" / "Resume" / "Retake", and so a half-finished
// run can be picked up where it left off. Scoped by user id so a shared browser
// never leaks one account's progress to another.
//
// Shape stored under the key:
//   { status: 'in_progress', snapshot: {...resumable diagnostic state...} }
//   { status: 'completed' }
// Absent key = not started.

const keyFor = (userId) => `solveki-diagnostic:${userId ?? 'anon'}`;

export function readDiagnostic(userId) {
  try {
    const raw = localStorage.getItem(keyFor(userId));
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null; // corrupt/unavailable storage -> treat as not started
  }
}

export function saveDiagnosticProgress(userId, snapshot) {
  try {
    localStorage.setItem(keyFor(userId), JSON.stringify({ status: 'in_progress', snapshot }));
  } catch { /* ignore quota / serialization / privacy-mode errors */ }
}

export function markDiagnosticCompleted(userId) {
  try {
    localStorage.setItem(keyFor(userId), JSON.stringify({ status: 'completed' }));
  } catch { /* ignore */ }
}

export function clearDiagnostic(userId) {
  try {
    localStorage.removeItem(keyFor(userId));
  } catch { /* ignore */ }
}
