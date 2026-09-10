import { useQuery } from '@tanstack/react-query';
import { apiFetch } from './auth.js';
import TopicProgress from './TopicProgress.jsx';
import ProficiencyTrend from './ProficiencyTrend.jsx';
import './Teacher.css';

function fmtStatus(s) {
  return s.replace('_', ' ');
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

  if (isPending) return <div className="teacher-page teacher-page-wide"><p>Loading…</p></div>;
  if (error) return <div className="teacher-page teacher-page-wide"><p className="teacher-error">Failed to load student.</p></div>;

  return (
    <div className="teacher-page teacher-page-wide">
      <h1>{data.student.name}</h1>
      <p className="teacher-card-stat">{data.student.email}</p>

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
            <tr><th>Assignment</th><th>Class</th><th>Status</th><th>Topics practiced</th></tr>
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
                <td>{a.num_practiced}/{a.num_topics}</td>
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
