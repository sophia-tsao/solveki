import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch, localDay } from './auth.js';
import AssignmentsTable, { assignmentPhase } from './AssignmentsTable.jsx';
import ConfirmDialog from './ui/ConfirmDialog.jsx';
import PageHeader from './ui/PageHeader.jsx';
import Tabs from './ui/Tabs.jsx';
import { plural } from './ui/format.js';
import './Teacher.css';

const TABS = [
  { key: 'open', label: 'Open' },
  { key: 'past_due', label: 'Past due' },
  { key: 'unassigned', label: 'Not assigned' },
  { key: 'all', label: 'All' },
];

function TeacherAssignments({ onCreate, onOpen, onEdit }) {
  const queryClient = useQueryClient();
  const [confirming, setConfirming] = useState(null); // the assignment to delete
  const [pickedTab, setTab] = useState(null); // null: Open, or All when nothing is open
  const [search, setSearch] = useState('');
  const [classFilter, setClassFilter] = useState('');
  const today = localDay();

  const { data, isPending, error } = useQuery({
    queryKey: ['teacher', 'assignments'],
    queryFn: async () => {
      const res = await apiFetch('/assignments/');
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
  });

  const refresh = () => queryClient.invalidateQueries({ queryKey: ['teacher'] });

  const remove = useMutation({
    mutationFn: async (id) => {
      const res = await apiFetch(`/assignments/${id}/`, { method: 'DELETE' });
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
    onSuccess: () => {
      setConfirming(null);
      refresh();
    },
  });

  const duplicate = useMutation({
    mutationFn: async (id) => {
      const res = await apiFetch(`/assignments/${id}/duplicate/`, { method: 'POST' });
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
    onSuccess: (copy) => {
      refresh();
      onEdit(copy.id);
    },
  });

  const all = data?.assignments || [];
  const classes = [];
  const seen = new Set();
  for (const a of all) {
    for (const c of a.classes || []) {
      if (!seen.has(c.class_id)) {
        seen.add(c.class_id);
        classes.push(c);
      }
    }
  }
  const phase = (a) => assignmentPhase(a);
  const tabCounts = Object.fromEntries(TABS.map((t) => [t.key, t.key === 'all' ? all.length : all.filter((a) => phase(a) === t.key).length]));
  const tab = pickedTab ?? (tabCounts.open ? 'open' : 'all');
  const q = search.trim().toLowerCase();
  const shown = all.filter((a) => (tab === 'all' || phase(a) === tab)
    && (!q || a.title.toLowerCase().includes(q))
    && (!classFilter || (a.classes || []).some((c) => String(c.class_id) === classFilter)));

  const tabs = TABS.filter((t) => t.key !== 'unassigned' || tabCounts.unassigned > 0)
    .map((t) => ({ ...t, count: tabCounts[t.key] }));

  return (
    <div className="teacher-page">
      <PageHeader
        title="Assignments"
        sub={data && `${plural(all.length, 'assignment')} · ${tabCounts.open} open`}
        actions={<button className="teacher-button" onClick={onCreate}>+ New assignment</button>}
      />

      {isPending && <p>Loading…</p>}
      {error && <p className="teacher-error">Failed to load assignments.</p>}
      {data && (all.length === 0 ? (
        <div className="teacher-box teacher-empty-state">
          <h2>No assignments yet</h2>
          <p>An assignment adds topics to your students’ daily practice and tracks who finishes them.</p>
          <button className="teacher-button" onClick={onCreate}>Create your first assignment</button>
        </div>
      ) : (
        <>
          <Tabs label="Assignment status" tabs={tabs} value={tab} onChange={setTab} />
          <div className="teacher-toolbar">
            <input
              type="search"
              className="teacher-input"
              placeholder="Search assignments"
              aria-label="Search assignments"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            {classes.length > 1 && (
              <select
                className="teacher-select"
                aria-label="Class"
                value={classFilter}
                onChange={(e) => setClassFilter(e.target.value)}
              >
                <option value="">All classes</option>
                {classes.map((c) => <option key={c.class_id} value={c.class_id}>{c.class_name}</option>)}
              </select>
            )}
          </div>
          {shown.length === 0 ? (
            <p className="teacher-empty">No assignments match.</p>
          ) : (
            <AssignmentsTable
              assignments={shown}
              today={today}
              onOpen={onOpen}
              actions={(a) => [
                { label: 'View results', onSelect: () => onOpen(a.id) },
                { label: 'Edit', onSelect: () => onEdit(a.id) },
                { label: 'Duplicate', onSelect: () => duplicate.mutate(a.id) },
                { label: 'Delete', danger: true, onSelect: () => setConfirming(a) },
              ]}
            />
          )}
        </>
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
