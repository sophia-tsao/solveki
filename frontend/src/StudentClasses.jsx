import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './auth.js';
import { createLogger } from './logger.js';
import './StudentClasses.css';

const log = createLogger('student-classes');

function StudentClasses() {
  const queryClient = useQueryClient();
  const [code, setCode] = useState('');
  const [joinMessage, setJoinMessage] = useState(null);

  const { data, isPending, error } = useQuery({
    queryKey: ['classes', 'mine'],
    queryFn: async () => {
      const res = await apiFetch('/classes/mine/');
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
  });

  const join = useMutation({
    mutationFn: async (joinCode) => {
      const res = await apiFetch('/classes/join/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: joinCode }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || `HTTP error! Status: ${res.status}`);
      return body;
    },
    onSuccess: (cls) => {
      log.info('Joined class', cls.id);
      setJoinMessage(`Joined "${cls.name}"`);
      setCode('');
      queryClient.invalidateQueries({ queryKey: ['classes', 'mine'] });
    },
    onError: (err) => setJoinMessage(err.message),
  });

  return (
    <div className="student-classes-page">
      <section className="student-classes-join">
        <h2>Join a class</h2>
        <div className="student-classes-join-row">
          <input
            className="student-classes-join-input"
            placeholder="Enter class code"
            value={code}
            onChange={(e) => setCode(e.target.value)}
          />
          <button
            className="student-classes-join-button"
            disabled={!code.trim() || join.isPending}
            onClick={() => join.mutate(code.trim())}
          >
            Join
          </button>
        </div>
        {joinMessage && <p className="student-classes-join-message">{joinMessage}</p>}
      </section>

      <h1>My classes</h1>
      {isPending && <p>Loading…</p>}
      {error && <p className="student-classes-error">Failed to load classes.</p>}

      {data && (data.classes.length === 0 ? (
        <p className="student-classes-empty">
          You haven't joined any classes yet. Enter a class code above to join one.
        </p>
      ) : (
        <ul className="student-classes-list">
          {data.classes.map((c) => (
            <li key={c.id} className="student-classes-item">
              <span className="student-classes-item-title">{c.name}</span>
              <span className="student-classes-item-meta">{c.teacher}</span>
            </li>
          ))}
        </ul>
      ))}
    </div>
  );
}

export default StudentClasses;
