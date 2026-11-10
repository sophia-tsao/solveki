import { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './auth.js';
import { createLogger } from './logger.js';
import AssignmentTopicPicker from './AssignmentTopicPicker.jsx';
import './Teacher.css';

const log = createLogger('assignment-builder');

function AssignmentBuilder({ assignmentId, onDone }) {
  const queryClient = useQueryClient();
  const editing = assignmentId != null;

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [deckSize, setDeckSize] = useState(10);
  const [allowLate, setAllowLate] = useState(true);
  const [selected, setSelected] = useState({}); // topic_id -> 1 (presence = selected)
  const [classDue, setClassDue] = useState({}); // class_id -> due_at (datetime-local string) | null
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const classesQuery = useQuery({
    queryKey: ['classes'],
    queryFn: async () => {
      const res = await apiFetch('/classes/');
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
  });

  // When editing, load the assignment and hydrate the form.
  const existingQuery = useQuery({
    queryKey: ['assignment', assignmentId],
    queryFn: async () => {
      const res = await apiFetch(`/assignments/${assignmentId}/`);
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
    enabled: editing,
  });

  useEffect(() => {
    const a = existingQuery.data;
    if (!a) return;
    setTitle(a.title);
    setDescription(a.description || '');
    setDeckSize(a.deck_size || 10);
    setAllowLate(a.allow_late ?? true);
    const sel = {};
    for (const t of a.topics || []) sel[t.topic_id] = 1;
    setSelected(sel);
    const due = {};
    for (const c of a.classes || []) due[c.class_id] = c.due_at ? c.due_at.slice(0, 16) : null;
    setClassDue(due);
  }, [existingQuery.data]);

  function toggleTopic(topicId) {
    setSelected((prev) => {
      const next = { ...prev };
      if (next[topicId] != null) delete next[topicId];
      else next[topicId] = 1;
      return next;
    });
  }

  function toggleClass(classId) {
    setClassDue((prev) => {
      const next = { ...prev };
      if (classId in next) delete next[classId];
      else next[classId] = null;
      return next;
    });
  }

  async function save() {
    setError(null);
    if (!title.trim()) { setError('Title is required'); return; }
    if (Object.keys(selected).length === 0) {
      setError('Select at least one topic to add to students’ decks.');
      return;
    }
    setSaving(true);
    try {
      const payload = {
        title: title.trim(),
        description,
        deck_size: deckSize,
        allow_late: allowLate,
        topics: Object.keys(selected).map((topic_id) => ({ topic_id: Number(topic_id) })),
      };

      const path = editing ? `/assignments/${assignmentId}/` : '/assignments/';
      const method = editing ? 'PATCH' : 'POST';
      const res = await apiFetch(path, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || `HTTP error! Status: ${res.status}`);
      const id = body.id;

      // Assign to the selected classes (replaces existing assignment links).
      const classes = Object.entries(classDue).map(([class_id, due]) => ({
        class_id: Number(class_id),
        due_at: due ? new Date(due).toISOString() : null,
      }));
      const assignRes = await apiFetch(`/assignments/${id}/assign/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ classes }),
      });
      if (!assignRes.ok) throw new Error(`Failed to assign to classes (${assignRes.status})`);

      log.info('Saved assignment', id);
      queryClient.invalidateQueries({ queryKey: ['teacher', 'assignments'] });
      onDone();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  const classes = classesQuery.data?.classes || [];

  return (
    <div className="teacher-page">
      <h1>{editing ? 'Edit assignment' : 'New assignment'}</h1>

      <div className="tg-note info">
        <span className="tg-note-icon">ℹ</span>
        <span>
          Choose the topics to add to your students&rsquo; practice and the fewest
          cards they should answer on them. Assigning it adds those topics to each
          enrolled student&rsquo;s deck (and to anyone who joins the class later) and
          spreads the cards over their daily practice until the due date; spaced
          repetition (SM-2) schedules the reviews automatically. Students who
          struggle get extra cards. The report shows each student&rsquo;s completion
          and where they stand on these topics.
        </span>
      </div>

      <div className="teacher-field">
        <label>Title</label>
        <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} />
      </div>
      <div className="teacher-field">
        <label>Description</label>
        <textarea rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
      </div>

      <div className="teacher-field">
        <label>Topics to add to students&rsquo; decks</label>
        <p className="teacher-help">
          Select topics from any courses below. They&rsquo;re added to every assigned
          student&rsquo;s practice automatically &mdash; students don&rsquo;t need to
          have picked them first.
        </p>
        <AssignmentTopicPicker selected={selected} onToggleTopic={toggleTopic} />
      </div>

      <div className="teacher-field">
        <label htmlFor="assignment-deck-size">Minimum cards</label>
        <p className="teacher-help">
          Students who get these topics right finish after this many cards on them.
          Students who struggle get more practice, up to {Math.ceil(deckSize * 1.5)} cards.
        </p>
        <input
          id="assignment-deck-size"
          type="number"
          min={1}
          value={deckSize}
          onChange={(e) => setDeckSize(Math.max(1, parseInt(e.target.value, 10) || 1))}
        />
      </div>

      <div className="teacher-field">
        <label>
          <input
            type="checkbox"
            checked={allowLate}
            onChange={(e) => setAllowLate(e.target.checked)}
          />
          {' '}Allow late work
        </label>
        <p className="teacher-help">
          When on, cards answered after the due date still count (and the finish is
          marked late). When off, progress stops at the due date.
        </p>
      </div>

      <h2>Assign to classes</h2>
      {classes.length === 0 ? (
        <p className="teacher-empty">Create a class first to assign this.</p>
      ) : (
        classes.map((c) => {
          const isSelected = c.id in classDue;
          return (
            <div key={c.id} className={`ab-class-row${isSelected ? ' selected' : ''}`}>
              <label className="ab-class-name">
                <input type="checkbox" checked={isSelected} onChange={() => toggleClass(c.id)} />
                {c.name}
              </label>
              {isSelected && (
                <label className="ab-due">
                  <span className="ab-due-label">Due</span>
                  <input
                    type="datetime-local"
                    className="ab-due-input"
                    value={classDue[c.id] || ''}
                    onChange={(e) => setClassDue((prev) => ({ ...prev, [c.id]: e.target.value || null }))}
                    aria-label={`Due date for ${c.name}`}
                  />
                </label>
              )}
            </div>
          );
        })
      )}

      {error && <p className="teacher-error">{error}</p>}
      <div className="teacher-header" style={{ marginTop: '1.5rem' }}>
        <button className="teacher-button secondary" onClick={onDone} disabled={saving}>Cancel</button>
        <button className="teacher-button" onClick={save} disabled={saving}>
          {saving ? 'Saving…' : 'Save assignment'}
        </button>
      </div>
    </div>
  );
}

export default AssignmentBuilder;
