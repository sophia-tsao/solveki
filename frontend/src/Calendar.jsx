import { useQuery } from '@tanstack/react-query';
import './Calendar.css';
import { apiFetch, localDay } from './auth.js';
import { createLogger } from './logger.js';

const log = createLogger('calendar');

async function fetchCalendar() {
  const response = await apiFetch(`/practice-calendar/?today=${localDay()}`);
  if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
  const result = await response.json();
  log.debug(`Loaded calendar ${result.year}-${result.month}`);
  return result;
}

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];
const WEEKDAYS = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];

// Practice calendar for the current month: each day the user finished the whole
// deck (completed), got partway (partial), or didn't practice (none).
function Calendar() {
  const { data, error } = useQuery({
    queryKey: ['practice-calendar', localDay()],
    queryFn: fetchCalendar,
  });

  if (error) {
    return (
      <section className="dash-calendar">
        <p className="dash-error">Error: {error.message}</p>
      </section>
    );
  }
  if (!data) return <section className="dash-calendar" aria-busy="true" />;

  const { year, month, days } = data;
  // Local, date-only math — no timezone drift since each Date is built from
  // explicit year/month/day at local midnight.
  const firstWeekday = new Date(year, month - 1, 1).getDay();
  const daysInMonth = new Date(year, month, 0).getDate();
  const todayIso = localDay();

  const iso = (d) =>
    `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`;

  const cells = [];
  for (let i = 0; i < firstWeekday; i += 1) cells.push(null);
  for (let d = 1; d <= daysInMonth; d += 1) cells.push(d);

  return (
    <section className="dash-calendar">
      <h2 className="cal-title">{MONTHS[month - 1]} {year}</h2>
      <div className="cal-grid" role="grid" aria-label="Practice by day">
        {WEEKDAYS.map((w, i) => (
          <span key={`wd-${i}`} className="cal-weekday">{w}</span>
        ))}
        {cells.map((d, i) => {
          if (d === null) return <span key={`blank-${i}`} className="cal-blank" />;
          const dateIso = iso(d);
          const status = days[dateIso] || 'none';
          const isToday = dateIso === todayIso;
          return (
            <span
              key={dateIso}
              className={`cal-day cal-day-${status}${isToday ? ' cal-today' : ''}`}
              title={`${dateIso}: ${status === 'none' ? 'not practiced' : status}`}
            >
              {d}
            </span>
          );
        })}
      </div>
      <ul className="cal-legend">
        <li><span className="cal-swatch cal-day-completed" />Completed</li>
        <li><span className="cal-swatch cal-day-partial" />Partial</li>
        <li><span className="cal-swatch cal-day-none" />Not practiced</li>
      </ul>
    </section>
  );
}

export default Calendar;
