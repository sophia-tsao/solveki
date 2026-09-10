import { useQuery } from '@tanstack/react-query';
import { apiFetch } from './auth.js';
import TopicProgress from './TopicProgress.jsx';
import './Teacher.css';

function pct(acc) {
  return acc == null ? '—' : `${Math.round(acc * 100)}%`;
}

function StudentDetail({ studentId }) {
  const { data, isPending, error } = useQuery({
    queryKey: ['teacher', 'student', studentId],
    queryFn: async () => {
      const res = await apiFetch(`/teacher/students/${studentId}/`);
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
    enabled: studentId != null,
  });

  if (isPending) return <div className="teacher-page"><p>Loading…</p></div>;
  if (error) return <div className="teacher-page"><p className="teacher-error">Failed to load student.</p></div>;

  return (
    <div className="teacher-page">
      <h1>{data.student.name}</h1>
      <p className="teacher-card-stat">{data.student.email}</p>

      <h2>Assignments</h2>
      {data.assignments.length === 0 ? (
        <p className="teacher-empty">No assignments yet.</p>
      ) : (
        <table className="teacher-table">
          <thead>
            <tr><th>Assignment</th><th>Class</th><th>Status</th><th>Accuracy</th><th>Answered</th></tr>
          </thead>
          <tbody>
            {data.assignments.map((a) => (
              <tr key={a.assignment_id}>
                <td>{a.title}</td>
                <td>{a.class_name}</td>
                <td>{a.status.replace('_', ' ')}</td>
                <td>{pct(a.accuracy)}</td>
                <td>{a.answered}</td>
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
