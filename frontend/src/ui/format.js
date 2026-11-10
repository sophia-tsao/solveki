// Shared display formatting for the teacher pages.

const DAY_MS = 24 * 60 * 60 * 1000;

// A local calendar day ('YYYY-MM-DD') as a Date at local midnight.
const dayDate = (iso) => new Date(`${iso.slice(0, 10)}T00:00`);

// "Nov 12"
export function fmtShortDate(iso) {
  if (!iso) return '—';
  const d = iso.length > 10 ? new Date(iso) : dayDate(iso);
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

// "Thu, Nov 12, 11:59 PM"
export function fmtDueDate(iso) {
  if (!iso) return 'No due date';
  return new Date(iso).toLocaleString(undefined, {
    weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
  });
}

// Whole days from `today` to the date of `iso` (negative in the past).
export function daysFrom(iso, today) {
  const target = iso.length > 10 ? new Date(iso) : dayDate(iso);
  const t = new Date(target.getFullYear(), target.getMonth(), target.getDate());
  return Math.round((t - dayDate(today)) / DAY_MS);
}

// A past day relative to today: "Today", "Yesterday", "5 days ago", or "Never".
export function fmtLastActive(iso, today) {
  if (!iso) return 'Never';
  const n = -daysFrom(iso, today);
  if (n <= 0) return 'Today';
  if (n === 1) return 'Yesterday';
  if (n < 14) return `${n} days ago`;
  return fmtShortDate(iso);
}

// A due date relative to today: "today", "tomorrow", "in 3 days", "2 days ago".
export function fmtRelativeDue(iso, today) {
  if (!iso) return '';
  const n = daysFrom(iso, today);
  if (n === 0) return 'today';
  if (n === 1) return 'tomorrow';
  if (n === -1) return 'yesterday';
  return n > 0 ? `in ${n} days` : `${-n} days ago`;
}

// A duration in seconds as "1h 5m", "12m" or "45s".
export function fmtDuration(seconds) {
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m ? `${h}h ${m}m` : `${h}h`;
}

export const plural = (n, one, many = `${one}s`) => `${n} ${n === 1 ? one : many}`;
