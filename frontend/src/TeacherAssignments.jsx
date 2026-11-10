import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './auth.js';
import ConfirmDialog from './ui/ConfirmDialog.jsx';
import OverflowMenu from './ui/OverflowMenu.jsx';
import './Teacher.css';

function TeacherAssignments({ onCreate, onOpen, onEdit }) {
  const queryClient = useQueryClient();
  const [confirming, setConfirming] = useState(null); // the assignment to delete

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
    onSuccess: () => {
      setConfirming(null);
      queryClient.invalidateQueries({ queryKey: ['teacher', 'assignments'] });
    },
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
            <tr><th>Title</th><th></th></tr>
          </thead>
          <tbody>
            {data.assignments.map((a) => (
              <tr key={a.id}>
                <td className="clickable" onClick={() => onOpen(a.id)}>{a.title}</td>
                <td className="num">
                  <OverflowMenu
                    label={`Actions for ${a.title}`}
                    items={[
                      { label: 'View results', onSelect: () => onOpen(a.id) },
                      { label: 'Edit', onSelect: () => onEdit(a.id) },
                      { label: 'Delete', danger: true, onSelect: () => setConfirming(a) },
                    ]}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ))}
      <ConfirmDialog
        open={confirming != null}
        title={`Delete "${confirming?.title}"?`}
        body="Students lose this assignment and its results. This can't be undone."
        confirmLabel="Delete assignment"
        busy={remove.isPending}
        onCancel={() => setConfirming(null)}
        onConfirm={() => remove.mutate(confirming.id)}
      />
    </div>
  );
}

export default TeacherAssignments;
