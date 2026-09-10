import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './auth.js';
import './Teacher.css';

function ClassList({ onOpenClass }) {
  const queryClient = useQueryClient();
  const [name, setName] = useState('');

  const { data, isPending, error } = useQuery({
    queryKey: ['classes'],
    queryFn: async () => {
      const res = await apiFetch('/classes/');
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
  });

  const create = useMutation({
    mutationFn: async (className) => {
      const res = await apiFetch('/classes/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: className }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || `HTTP error! Status: ${res.status}`);
      return body;
    },
    onSuccess: () => {
      setName('');
      queryClient.invalidateQueries({ queryKey: ['classes'] });
    },
  });

  return (
    <div className="teacher-page">
      <h1>Classes</h1>
      <div className="teacher-header">
        <input
          className="teacher-field"
          style={{ flex: 1, padding: '0.5rem 0.75rem', border: '1px solid #ccc', borderRadius: 8 }}
          placeholder="New class name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button
          className="teacher-button"
          disabled={!name.trim() || create.isPending}
          onClick={() => create.mutate(name.trim())}
        >
          Create class
        </button>
      </div>

      {isPending && <p>Loading…</p>}
      {error && <p className="teacher-error">Failed to load classes.</p>}
      {data && (data.classes.length === 0 ? (
        <p className="teacher-empty">No classes yet. Create one above.</p>
      ) : (
        <div className="teacher-cards">
          {data.classes.map((c) => (
            <button key={c.id} className="teacher-card" onClick={() => onOpenClass(c.id)}>
              <div className="teacher-card-title">{c.name}</div>
              <div className="teacher-card-stat">{c.student_count} students</div>
              <div className="teacher-card-stat">Code: <span className="teacher-code">{c.join_code}</span></div>
            </button>
          ))}
        </div>
      ))}
    </div>
  );
}

export default ClassList;
