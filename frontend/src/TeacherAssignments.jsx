import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './auth.js';
import './Teacher.css';

function TeacherAssignments({ onCreate, onOpen, onEdit }) {
  const queryClient = useQueryClient();

  const { data, isPending, error } = useQuery({
    queryKey: ['teacher', 'assignments'],
    queryFn: async () => {
      const res = await apiFetch('/assignments/');
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
  });

  const remove = useMutation({
    mutationFn: async (id) => {
      const res = await apiFetch(`/assignments/${id}/`, { method: 'DELETE' });
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['teacher', 'assignments'] }),
  });

  return (
    <div className="teacher-page">
      <div className="teacher-header">
        <h1>Assignments</h1>
        <button className="teacher-button" onClick={onCreate}>New assignment</button>
      </div>

      {isPending && <p>Loading…</p>}
      {error && <p className="teacher-error">Failed to load assignments.</p>}
      {data && (data.assignments.length === 0 ? (
        <p className="teacher-empty">No assignments yet. Create one to get started.</p>
      ) : (
        <table className="teacher-table">
          <thead>
            <tr><th>Title</th><th>SM-2</th><th></th></tr>
          </thead>
          <tbody>
            {data.assignments.map((a) => (
              <tr key={a.id}>
                <td className="clickable" onClick={() => onOpen(a.id)}>{a.title}</td>
                <td>{a.mode?.endsWith('_sm2') ? 'On' : 'Off'}</td>
                <td style={{ display: 'flex', gap: '0.4rem' }}>
                  <button className="teacher-button secondary" onClick={() => onOpen(a.id)}>Results</button>
                  <button className="teacher-button secondary" onClick={() => onEdit(a.id)}>Edit</button>
                  <button className="teacher-button danger" onClick={() => remove.mutate(a.id)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ))}
    </div>
  );
}

export default TeacherAssignments;
