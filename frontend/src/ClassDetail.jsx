import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch, localDay } from './auth.js';
import { BandBar, BandLegend } from './BandBar.jsx';
import AssignmentsTable, { assignmentPhase } from './AssignmentsTable.jsx';
import ClassProgressGrid from './ClassProgressGrid.jsx';
import ConfirmDialog from './ui/ConfirmDialog.jsx';
import OverflowMenu from './ui/OverflowMenu.jsx';
import PageHeader from './ui/PageHeader.jsx';
import { StatusChip } from './ui/StatusChip.jsx';
import Tabs from './ui/Tabs.jsx';
import { useSortable } from './ui/useSortable.js';
import { fmtLastActive, plural } from './ui/format.js';
import './Teacher.css';

const TAB_KEYS = ['students', 'progress', 'assignments', 'settings'];

function getJson(path) {
  return async () => {
    const res = await apiFetch(path);
    if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
    return res.json();
  };
}

function Roster({ students, today, onOpenStudent, onRemove }) {
  const { rows, headerProps, ariaSort } = useSortable(students, {
    name: (s) => s.name.toLowerCase(),
    week: (s) => s.cards_7d,
    accuracy: (s) => s.accuracy_7d,
    last: (s) => s.last_active,
    overdue: (s) => s.overdue_count,
  });
  const th = (key, label, extra = {}) => (
    <th aria-sort={ariaSort(key)} {...extra}><button {...headerProps(key)}>{label}</button></th>
  );
  return (
    <div className="teacher-box teacher-scroll">
      <table className="teacher-table">
        <thead>
          <tr>
            {th('name', 'Name')}
            <th>Email</th>
            <th>Familiarity</th>
            {th('week', 'Cards (7d)', { className: 'num' })}
            {th('accuracy', 'Accuracy (7d)', { className: 'num' })}
            {th('last', 'Last active')}
            {th('overdue', 'Overdue')}
            <th><span className="visually-hidden">Actions</span></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((s) => (
            <tr key={s.id}>
              <td>
                <button type="button" className="teacher-link" onClick={() => onOpenStudent(s.id)}>{s.name}</button>
              </td>
              <td className="teacher-muted">{s.email}</td>
              <td style={{ minWidth: '140px' }}><BandBar counts={s.proficiency || {}} /></td>
              <td className="num">{s.cards_7d ?? '—'}</td>
              <td className="num">{s.accuracy_7d == null ? '—' : `${s.accuracy_7d}%`}</td>
              <td>{s.last_active === undefined ? '—' : fmtLastActive(s.last_active, today)}</td>
              <td>
                {s.overdue_count
                  ? <StatusChip status="overdue" label={`${s.overdue_count} overdue`} />
                  : <span className="teacher-muted">—</span>}
              </td>
              <td className="num">
                <OverflowMenu
                  label={`Actions for ${s.name}`}
                  items={[
                    { label: 'Open student', onSelect: () => onOpenStudent(s.id) },
                    { label: 'Remove from class', danger: true, onSelect: () => onRemove(s) },
                  ]}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ClassSettings({ cls, onSaved, onArchived }) {
  const queryClient = useQueryClient();
  const [name, setName] = useState(cls.name);
  const [confirmArchive, setConfirmArchive] = useState(false);

  const patch = useMutation({
    mutationFn: async (body) => {
      const res = await apiFetch(`/classes/${cls.id}/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || `HTTP error! Status: ${res.status}`);
      return data;
    },
    onSuccess: (data, body) => {
      queryClient.invalidateQueries({ queryKey: ['classes'] });
      queryClient.invalidateQueries({ queryKey: ['class', cls.id] });
      queryClient.invalidateQueries({ queryKey: ['teacher'] });
      if (body.archived) onArchived();
      else onSaved?.();
    },
  });

  return (
    <div className="teacher-box teacher-box-body class-settings">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (name.trim()) patch.mutate({ name: name.trim() });
        }}
      >
        <div className="teacher-field">
          <label htmlFor="class-name">Class name</label>
          <div className="teacher-toolbar" style={{ margin: 0 }}>
            <input id="class-name" type="text" className="teacher-input" value={name} onChange={(e) => setName(e.target.value)} />
            <button type="submit" className="teacher-button" disabled={!name.trim() || name.trim() === cls.name || patch.isPending}>
              Save name
            </button>
          </div>
        </div>
      </form>
      <div className="teacher-field">
        <label>Join code</label>
        <p className="teacher-help">
          Students enter <span className="teacher-code">{cls.join_code}</span> on their Classes page to join.
        </p>
      </div>
      <div className="teacher-field">
        <label>Archive</label>
        <p className="teacher-help">
          Archiving hides the class from your lists. Students and their progress are kept.
        </p>
        <div>
          <button type="button" className="teacher-button secondary" onClick={() => setConfirmArchive(true)}>
            Archive class
          </button>
        </div>
      </div>
      {patch.error && <p className="teacher-error">{patch.error.message}</p>}
      <ConfirmDialog
        open={confirmArchive}
        title={`Archive ${cls.name}?`}
        body="It disappears from your classes and home page. Students keep their progress."
        confirmLabel="Archive class"
        busy={patch.isPending}
        onCancel={() => setConfirmArchive(false)}
        onConfirm={() => patch.mutate({ archived: true })}
      />
    </div>
  );
}

function ClassDetail({ classId, tab: tabParam, onTabChange, onBack, onOpenStudent, onOpenAssignment }) {
  const queryClient = useQueryClient();
  const [confirming, setConfirming] = useState(null); // the student to remove
  const [localTab, setLocalTab] = useState('students');
  const [copied, setCopied] = useState(false);
  const tab = TAB_KEYS.includes(tabParam) ? tabParam : (onTabChange ? 'students' : localTab);
  const setTab = onTabChange || setLocalTab;
  const today = localDay();

  const classQuery = useQuery({
    queryKey: ['class', classId],
    queryFn: getJson(`/classes/${classId}/`),
    enabled: classId != null,
  });

  const studentsQuery = useQuery({
    queryKey: ['class', classId, 'students'],
    queryFn: getJson(`/classes/${classId}/students/?today=${today}`),
    enabled: classId != null,
  });

  const assignmentsQuery = useQuery({
    queryKey: ['teacher', 'assignments', 'class', classId],
    queryFn: getJson(`/assignments/?class=${classId}`),
    enabled: classId != null,
  });

  const remove = useMutation({
    mutationFn: async (studentId) => {
      const res = await apiFetch(`/classes/${classId}/students/${studentId}/`, { method: 'DELETE' });
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
    onSuccess: () => {
      setConfirming(null);
      queryClient.invalidateQueries({ queryKey: ['class', classId] });
    },
  });

  const cls = classQuery.data;
  const students = studentsQuery.data?.students || [];
  const assignments = assignmentsQuery.data?.assignments || [];
  const open = assignments.filter((a) => assignmentPhase(a) === 'open').length;
  const active = students.filter((s) => s.cards_7d > 0).length;

  async function copyCode() {
    try {
      await navigator.clipboard.writeText(cls.join_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="teacher-page">
      <PageHeader
        crumbs={[{ label: 'Classes', onClick: onBack }, { label: cls ? cls.name : 'Class' }]}
        title={cls ? cls.name : 'Class'}
        sub={cls && studentsQuery.data && [
          plural(students.length, 'student'),
          assignmentsQuery.data && plural(open, 'open assignment'),
          `${active} active this week`,
        ].filter(Boolean).join(' · ')}
        actions={cls && (
          <>
            <span className="teacher-muted">Join code</span>
            <span className="teacher-code">{cls.join_code}</span>
            <button type="button" className="teacher-button secondary small" onClick={copyCode}>
              {copied ? 'Copied' : 'Copy'}
            </button>
          </>
        )}
      />

      <Tabs
        label="Class"
        value={tab}
        onChange={setTab}
        tabs={[
          { key: 'students', label: 'Students', count: studentsQuery.data ? students.length : undefined },
          { key: 'progress', label: 'Progress' },
          { key: 'assignments', label: 'Assignments', count: assignmentsQuery.data ? assignments.length : undefined },
          { key: 'settings', label: 'Settings' },
        ]}
      />

      {tab === 'students' && (
        <>
          {studentsQuery.isPending && <p>Loading…</p>}
          {studentsQuery.data && (students.length === 0 ? (
            <div className="teacher-box teacher-empty-state">
              <h2>No students yet</h2>
              <p>
                Students join from their Classes page with the code{' '}
                <span className="teacher-code">{cls?.join_code}</span>.
              </p>
            </div>
          ) : (
            <>
              <div className="teacher-toolbar"><BandLegend /></div>
              <Roster students={students} today={today} onOpenStudent={onOpenStudent} onRemove={setConfirming} />
            </>
          ))}
        </>
      )}

      {tab === 'progress' && <ClassProgressGrid classId={classId} onOpenStudent={onOpenStudent} />}

      {tab === 'assignments' && (
        assignmentsQuery.isPending ? <p>Loading…</p> : assignments.length === 0 ? (
          <div className="teacher-box teacher-empty-state">
            <h2>No assignments yet</h2>
            <p>Assignments you give this class show here with who has finished them.</p>
          </div>
        ) : (
          <AssignmentsTable
            assignments={assignments}
            today={today}
            showClasses={false}
            onOpen={(aid) => onOpenAssignment?.(aid)}
          />
        )
      )}

      {tab === 'settings' && cls && <ClassSettings key={cls.name} cls={cls} onArchived={onBack} />}

      <ConfirmDialog
        open={confirming != null}
        title={`Remove ${confirming?.name} from this class?`}
        body="They stop getting this class's assignments. They can rejoin with the join code."
        confirmLabel="Remove student"
        busy={remove.isPending}
        onCancel={() => setConfirming(null)}
        onConfirm={() => remove.mutate(confirming.id)}
      />
    </div>
  );
}

export default ClassDetail;
