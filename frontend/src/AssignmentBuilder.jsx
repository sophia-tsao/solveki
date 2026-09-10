import { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './auth.js';
import { createLogger } from './logger.js';
import AssignmentTopicPicker from './AssignmentTopicPicker.jsx';
import './Teacher.css';

const log = createLogger('assignment-builder');

// The backend stores the delivery kind (topics/deck) and the SM-2 flag together
// in one `mode` field; the form edits them as two separate controls.
function splitMode(mode) {
  return { kind: mode?.startsWith('deck') ? 'deck' : 'topics', sm2: !!mode?.endsWith('_sm2') };
}
function joinMode(kind, sm2) {
  return sm2 ? `${kind}_sm2` : kind;
}

function AssignmentBuilder({ assignmentId, onDone }) {
  const queryClient = useQueryClient();
  const editing = assignmentId != null;

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [kind, setKind] = useState('topics');
  const [sm2, setSm2] = useState(false);
  // Deck scope: 'all' (every selected topic) or 'topics' (a teacher-picked set).
  const [deckScope, setDeckScope] = useState('all');
  const [deckSize, setDeckSize] = useState(10);
  const [topicCounts, setTopicCounts] = useState({}); // topic_id -> num_questions
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
    const { kind: k, sm2: s } = splitMode(a.mode);
    setKind(k);
    setSm2(s);
    // Legacy course/unit-scoped decks collapse to 'all' (only 'all'/'topics' now).
    setDeckScope(a.deck_scope === 'topics' ? 'topics' : 'all');
    setDeckSize(a.deck_size || 10);
    const counts = {};
    for (const t of a.topics || []) counts[t.topic_id] = t.num_questions;
    setTopicCounts(counts);
    const due = {};
    for (const c of a.classes || []) due[c.class_id] = c.due_at ? c.due_at.slice(0, 16) : null;
    setClassDue(due);
  }, [existingQuery.data]);

  function toggleTopic(topicId) {
    setTopicCounts((prev) => {
      const next = { ...prev };
      if (next[topicId] != null) delete next[topicId];
      else next[topicId] = 1;
      return next;
    });
  }

  function setCount(topicId, value) {
    const n = Math.max(1, parseInt(value, 10) || 1);
    setTopicCounts((prev) => ({ ...prev, [topicId]: n }));
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
    const picksTopics = kind === 'topics' || (kind === 'deck' && deckScope === 'topics');
    if (picksTopics && Object.keys(topicCounts).length === 0) {
      setError('Select at least one topic.');
      return;
    }
    setSaving(true);
    try {
      const payload = {
        title: title.trim(),
        description,
        mode: joinMode(kind, sm2),
      };
      if (kind === 'topics') {
        payload.topics = Object.entries(topicCounts).map(([topic_id, num_questions]) => ({
          topic_id: Number(topic_id), num_questions,
        }));
      } else {
        payload.deck_scope = deckScope;
        payload.deck_size = deckSize;
        if (deckScope === 'topics') {
          // Selection-only: the deck size governs the total, so each topic just
          // needs to be present (count is ignored for a deck).
          payload.topics = Object.keys(topicCounts).map((topic_id) => ({
            topic_id: Number(topic_id), num_questions: 1,
          }));
        }
      }

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

      <div className="teacher-field">
        <label>Title</label>
        <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} />
      </div>
      <div className="teacher-field">
        <label>Description</label>
        <textarea rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
      </div>

      <div className="teacher-field">
        <label>Type</label>
        <select value={kind} onChange={(e) => setKind(e.target.value)}>
          <option value="topics">Pick topics &amp; question counts</option>
          <option value="deck">Student's spaced-repetition deck</option>
        </select>
        {kind === 'topics' ? (
          <div className="tg-flow" aria-label="How a topics assignment builds problems">
            <span className="tg-pill">Topics &amp; counts you pick</span>
            <span className="tg-arrow">→</span>
            <span className="tg-pill">Freshly generated per student</span>
            <span className="tg-arrow">→</span>
            <span className="tg-pill">Same topics, different problems</span>
          </div>
        ) : (
          <>
            <div className="tg-flow" aria-label="How a deck assignment builds problems">
              <span className="tg-pill">
                {deckScope === 'topics' ? 'Topics you pick' : "Each student's selected topics"}
              </span>
              <span className="tg-arrow">→</span>
              <span className="tg-pill">Weighted by what's due now</span>
              <span className="tg-arrow">→</span>
              <span className="tg-pill">{deckSize} question{deckSize === 1 ? '' : 's'}</span>
            </div>
            {deckScope === 'topics' ? (
              <div className="tg-note info">
                <span className="tg-note-icon">ℹ</span>
                <span>
                  The topics you pick below are added to every assigned student's practice
                  automatically — they don't need to have selected them first.
                </span>
              </div>
            ) : (
              <div className="tg-note warn">
                <span className="tg-note-icon">⚠</span>
                <span>
                  Draws from each student's <strong>own selected topics</strong>. A student who
                  hasn't selected any topics gets nothing to practice — make sure students have
                  set up their topics first, or use "Topics I pick" instead.
                </span>
              </div>
            )}
          </>
        )}
      </div>

      <div className="teacher-field">
        <label className="teacher-checkbox">
          <input type="checkbox" checked={sm2} onChange={(e) => setSm2(e.target.checked)} />
          <span>Count toward spaced-repetition schedule (SM-2)</span>
        </label>
        {sm2 ? (
          <div className="tg-sm2">
            <div className="tg-flow">
              <span className="tg-pill">Student finishes</span>
              <span className="tg-arrow">→</span>
              <span className="tg-pill">1 grade per topic, from their accuracy</span>
              <span className="tg-arrow">→</span>
              <span className="tg-pill">Next review date shifts</span>
            </div>
            <div className="tg-branch">
              <span className="tg-branch-key tg-up">Higher accuracy ↑</span>
              <span>topic comes back <strong>later</strong> (longer gap)</span>
              <span className="tg-branch-key tg-down">Lower accuracy ↓</span>
              <span>topic comes back <strong>sooner</strong> (shorter gap)</span>
            </div>
            <div className="tg-scale" aria-label="Accuracy to review grade">
              <span className="tg-scale-seg" style={{ background: '#dc2626' }}>&lt;40%<small>grade 1</small></span>
              <span className="tg-scale-seg" style={{ background: '#f97316' }}>40–59%<small>grade 2</small></span>
              <span className="tg-scale-seg" style={{ background: '#eab308' }}>60–74%<small>grade 3</small></span>
              <span className="tg-scale-seg" style={{ background: '#84cc16' }}>75–89%<small>grade 4</small></span>
              <span className="tg-scale-seg" style={{ background: '#16a34a' }}>90–100%<small>grade 5</small></span>
            </div>
            <p className="tg-fine">Applied once per topic when finished — and at most once per day per topic, shared with the student's normal daily practice.</p>
          </div>
        ) : (
          <div className="tg-note info">
            <span className="tg-note-icon">ℹ</span>
            <span>Standalone practice — finishing won't change any topic's review schedule.</span>
          </div>
        )}
      </div>

      {kind === 'topics' ? (
        <div className="teacher-field">
          <label>Topics &amp; question counts</label>
          <p className="teacher-help">
            Select topics from any courses below and set how many questions each student gets
            for each. Every student receives freshly generated problems of the same difficulty.
          </p>
          <AssignmentTopicPicker
            topicCounts={topicCounts}
            onToggleTopic={toggleTopic}
            onSetCount={setCount}
          />
        </div>
      ) : (
        <>
          <div className="teacher-field">
            <label>Deck scope</label>
            <select value={deckScope} onChange={(e) => setDeckScope(e.target.value)}>
              <option value="all">All the student's selected topics</option>
              <option value="topics">Topics I pick</option>
            </select>
            <div className="tg-note info">
              <span className="tg-note-icon">ℹ</span>
              <span>
                {deckScope === 'all'
                  ? 'Draws from everything each student has selected — whatever is due for them today.'
                  : "Restricts each student's deck to just the topics you check below."}
              </span>
            </div>
          </div>
          {deckScope === 'topics' && (
            <div className="teacher-field">
              <label>Topics</label>
              <AssignmentTopicPicker
                topicCounts={topicCounts}
                onToggleTopic={toggleTopic}
                onSetCount={setCount}
                showCounts={false}
              />
            </div>
          )}
          <div className="teacher-field">
            <label>Number of questions</label>
            <input type="number" min={1} value={deckSize} onChange={(e) => setDeckSize(Math.max(1, parseInt(e.target.value, 10) || 1))} />
          </div>
        </>
      )}

      <h2>Assign to classes</h2>
      {classes.length === 0 ? (
        <p className="teacher-empty">Create a class first to assign this.</p>
      ) : (
        classes.map((c) => {
          const selected = c.id in classDue;
          return (
            <div key={c.id} className="teacher-topic-row">
              <label style={{ flex: 1 }}>
                <input type="checkbox" checked={selected} onChange={() => toggleClass(c.id)} />
                {' '}{c.name}
              </label>
              {selected && (
                <input
                  type="datetime-local"
                  value={classDue[c.id] || ''}
                  onChange={(e) => setClassDue((prev) => ({ ...prev, [c.id]: e.target.value || null }))}
                />
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
