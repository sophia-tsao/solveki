import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './auth.js';
import PageHeader from './ui/PageHeader.jsx';
import { plural } from './ui/format.js';
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
      queryClient.invalidateQueries({ queryKey: ['teacher'] });
    },
  });

  return (
    <div className="teacher-page">
      <PageHeader
        title="Classes"
        sub={data && plural(data.classes.length, 'class', 'classes')}
        actions={(
          <form
            className="teacher-toolbar"
            style={{ margin: 0 }}
            onSubmit={(e) => {
              e.preventDefault();
              if (name.trim()) create.mutate(name.trim());
            }}
          >
            <input
              className="teacher-input"
              placeholder="New class name"
              aria-label="New class name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <button type="submit" className="teacher-button" disabled={!name.trim() || create.isPending}>
              Create class
            </button>
          </form>
        )}
      />
      {create.error && <p className="teacher-error">{create.error.message}</p>}

      {isPending && <p>Loading…</p>}
      {error && <p className="teacher-error">Failed to load classes.</p>}
      {data && (data.classes.length === 0 ? (
        <div className="teacher-box teacher-empty-state">
          <h2>No classes yet</h2>
          <p>Create a class above, then share its join code so students can join.</p>
        </div>
      ) : (
        <div className="teacher-cards">
          {data.classes.map((c) => (
            <button key={c.id} className="teacher-card class-card" onClick={() => onOpenClass(c.id)}>
              <div className="teacher-card-title">{c.name}</div>
              <div className="teacher-card-stat">{plural(c.student_count, 'student')}</div>
              <div className="teacher-card-stat">
                Join code <span className="teacher-code">{c.join_code}</span>
              </div>
            </button>
          ))}
        </div>
      ))}
    </div>
  );
}

export default ClassList;
