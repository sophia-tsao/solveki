import { useQuery } from '@tanstack/react-query';
import { apiFetch, localDay } from './auth.js';
import TopicProgress from './TopicProgress.jsx';
import ProficiencyTrend from './ProficiencyTrend.jsx';
import StruggledTopics from './StruggledTopics.jsx';
import './Teacher.css';

function fmtStatus(s) {
  return s.replace('_', ' ');
}

// A duration in seconds as "1h 5m", "12m" or "45s".
function fmtDuration(seconds) {
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m ? `${h}h ${m}m` : `${h}h`;
}

const DAY_LABEL = { completed: 'finished the deck', partial: 'practiced some', none: 'no practice' };

// How consistently, how much, and how well the student has practiced lately.
function PracticeActivity({ activity }) {
  const { days, days_practiced: practiced, streak, week } = activity;
  const today = days[days.length - 1]?.date;
  return (
    <div className="teacher-cards" style={{ marginTop: '1rem' }}>
      <div className="teacher-card static">
        <div className="teacher-card-title">Consistency</div>
        <div className="teacher-card-big">{practiced} of last {days.length} days</div>
        <div className="teacher-card-stat">
          {streak > 0 ? `${streak}-day streak` : 'No current streak'}
        </div>
        <div className="activity-strip" role="img" aria-label={`Practiced ${practiced} of the last ${days.length} days`}>
          {days.map((d) => (
            <span
              key={d.date}
              className={`activity-day ${d.status}${d.date === today ? ' today' : ''}`}
              title={`${d.date}: ${DAY_LABEL[d.status]}`}
            />
          ))}
        </div>
      </div>
      <div className="teacher-card static">
        <div className="teacher-card-title">Questions answered</div>
        <div className="teacher-card-big">{week.cards_answered}</div>
        <div className="teacher-card-stat">Last 7 days</div>
      </div>
      <div className="teacher-card static">
        <div className="teacher-card-title">Time reviewing</div>
        <div className="teacher-card-big">{fmtDuration(week.seconds)}</div>
        <div className="teacher-card-stat">Last 7 days</div>
      </div>
      <div className="teacher-card static">
        <div className="teacher-card-title">Accuracy</div>
        <div className="teacher-card-big">{week.accuracy == null ? '—' : `${week.accuracy}%`}</div>
        <div className="teacher-card-stat">Right on the first try, last 7 days</div>
      </div>
    </div>
  );
}

function StudentDetail({ studentId }) {
  const { data, isPending, error } = useQuery({
    queryKey: ['teacher', 'student', studentId],
    queryFn: async () => {
      const res = await apiFetch(`/teacher/students/${studentId}/?today=${localDay()}`);
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
    enabled: studentId != null,
  });

  if (isPending) return <div className="teacher-page teacher-page-wide"><p>Loading…</p></div>;
  if (error) return <div className="teacher-page teacher-page-wide"><p className="teacher-error">Failed to load student.</p></div>;

  return (
    <div className="teacher-page teacher-page-wide">
      <h1>{data.student.name}</h1>
      <p className="teacher-card-stat">{data.student.email}</p>

      <h2>Practice</h2>
      {data.activity && <PracticeActivity activity={data.activity} />}
      <StruggledTopics
        topics={data.struggled || []}
        emptyText="Nothing stands out — no misses in the last 30 days."
      />

      <ProficiencyTrend
        title="Familiarity over time"
        description="Share of this student's topics in each proficiency band, day by day."
        scope="student"
        studentId={data.student.id}
      />

      <h2>Assignments</h2>
      {data.assignments.length === 0 ? (
        <p className="teacher-empty">No assignments yet.</p>
      ) : (
        <table className="teacher-table">
          <thead>
            <tr><th>Assignment</th><th>Class</th><th>Status</th><th>Cards answered</th></tr>
          </thead>
          <tbody>
            {data.assignments.map((a) => (
              <tr key={a.assignment_id}>
                <td>{a.title}</td>
                <td>{a.class_name}</td>
                <td>
                  {fmtStatus(a.status)}
                  {a.overdue && <span className="teacher-overdue"> · overdue</span>}
                </td>
                <td>{a.cards_answered}/{a.deck_size}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h2>Topic progress</h2>
      {data.topics.length === 0 ? (
        <p className="teacher-empty">No topics selected.</p>
      ) : (
        <TopicProgress selected={data.topics} upcoming={data.upcoming || []} />
      )}
    </div>
  );
}

export default StudentDetail;
