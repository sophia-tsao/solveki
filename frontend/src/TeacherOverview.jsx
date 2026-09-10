import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiFetch } from './auth.js';
import ProficiencyTrend from './ProficiencyTrend.jsx';
import './Teacher.css';

function TeacherOverview({ onOpenClass }) {
  // "" = all students across every class; otherwise a specific class id.
  const [trendClass, setTrendClass] = useState('');

  const { data, isPending, error } = useQuery({
    queryKey: ['teacher', 'overview'],
    queryFn: async () => {
      const res = await apiFetch('/teacher/overview/');
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    },
  });

  return (
    <div className="teacher-page">
      <h1>Overview</h1>
      {isPending && <p>Loading…</p>}
      {error && <p className="teacher-error">Failed to load overview.</p>}
      {data && (
        <>
          <p className="teacher-card-stat">
            {data.total_students} student{data.total_students === 1 ? '' : 's'} across your classes
          </p>

          {/* Familiarity over time — one chart, scoped by the class dropdown. */}
          {(() => {
            const selected = data.classes.find((c) => String(c.id) === trendClass);
            return (
              <>
                {data.classes.length > 0 && (
                  <div className="teacher-field" style={{ maxWidth: '260px' }}>
                    <label htmlFor="trend-class">Show familiarity for</label>
                    <select
                      id="trend-class"
                      value={trendClass}
                      onChange={(e) => setTrendClass(e.target.value)}
                    >
                      <option value="">All classes</option>
                      {data.classes.map((c) => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                      ))}
                    </select>
                  </div>
                )}
                <ProficiencyTrend
                  key={trendClass || 'all'}
                  title={selected ? `Familiarity over time — ${selected.name}` : 'Familiarity over time — all students'}
                  description={
                    selected
                      ? 'Average share of topics in each proficiency band across this class.'
                      : 'Average share of topics in each proficiency band, across every student in your classes.'
                  }
                  scope={selected ? 'class' : 'all'}
                  classId={selected ? selected.id : undefined}
                />
              </>
            );
          })()}

          {data.classes.length === 0 ? (
            <p className="teacher-empty">You haven't created any classes yet.</p>
          ) : (
            <div className="teacher-cards">
              {data.classes.map((c) => (
                <button key={c.id} className="teacher-card" onClick={() => onOpenClass(c.id)}>
                  <div className="teacher-card-title">{c.name}</div>
                  <div className="teacher-card-stat">{c.student_count} students</div>
                </button>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default TeacherOverview;
