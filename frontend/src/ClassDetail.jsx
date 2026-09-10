import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './auth.js';
import './Teacher.css';

function ClassDetail({ classId, onBack, onOpenStudent }) {
  const queryClient = useQueryClient();

  const classQuery = useQuery({
    queryKey: ['class', classId],
    queryFn: async () => {
      const res = await apiFetch(`/classes/${classId}/`);
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
    enabled: classId != null,
  });

  const studentsQuery = useQuery({
    queryKey: ['class', classId, 'students'],
    queryFn: async () => {
      const res = await apiFetch(`/classes/${classId}/students/`);
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
    enabled: classId != null,
  });

  const remove = useMutation({
    mutationFn: async (studentId) => {
      const res = await apiFetch(`/classes/${classId}/students/${studentId}/`, { method: 'DELETE' });
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['class', classId, 'students'] }),
  });

  const cls = classQuery.data;
  const students = studentsQuery.data?.students || [];

  return (
    <div className="teacher-page">
      {onBack && (
        <button className="teacher-button secondary teacher-back" onClick={onBack}>
          ← Back to classes
        </button>
      )}
      <h1>{cls ? cls.name : 'Class'}</h1>
      {cls && (
        <p className="teacher-card-stat">
          Join code: <span className="teacher-code">{cls.join_code}</span> · {cls.student_count} students
        </p>
      )}

      <h2>Students</h2>
      {studentsQuery.isPending && <p>Loading…</p>}
      {students.length === 0 ? (
        <p className="teacher-empty">No students have joined yet. Share the join code above.</p>
      ) : (
        <table className="teacher-table">
          <thead>
            <tr><th>Name</th><th>Email</th><th>Joined</th><th></th></tr>
          </thead>
          <tbody>
            {students.map((s) => (
              <tr key={s.id}>
                <td className="clickable" onClick={() => onOpenStudent(s.id)}>{s.name}</td>
                <td>{s.email}</td>
                <td>{new Date(s.joined_at).toLocaleDateString()}</td>
                <td>
                  <button className="teacher-button danger" onClick={() => remove.mutate(s.id)}>Remove</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default ClassDetail;
