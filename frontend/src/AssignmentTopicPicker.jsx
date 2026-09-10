import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiFetch } from './auth.js';
import './AssignmentTopicPicker.css';

async function fetchCourses() {
  const res = await apiFetch('/courses/');
  if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
  return (await res.json()).courses;
}

async function fetchAllTopics() {
  const res = await apiFetch('/topics/');
  if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
  return (await res.json()).topics;
}

// Group a course's topics under their curriculum unit, preserving order.
function groupByUnit(topics) {
  const groups = [];
  const byKey = new Map();
  for (const t of topics) {
    const key = t.unit_key ?? '__none__';
    if (!byKey.has(key)) {
      const g = { key, name: t.unit_name || null, topics: [] };
      byKey.set(key, g);
      groups.push(g);
    }
    byKey.get(key).topics.push(t);
  }
  return groups;
}

/**
 * A courses-page-style picker for choosing topics across multiple courses.
 * Selection lives in the parent as `selected` (a topic_id -> truthy map); this
 * component only reads it and calls `onToggleTopic` to mutate it. It's a
 * selection-only picker — assignments add the chosen topics to students' decks,
 * and a single deck size (set elsewhere) governs how many cards they hold.
 */
function AssignmentTopicPicker({ selected, onToggleTopic }) {
  const [expanded, setExpanded] = useState(() => new Set());
  const [search, setSearch] = useState('');

  const { data: courses = [], error: coursesError } = useQuery({
    queryKey: ['courses'],
    queryFn: fetchCourses,
  });
  const { data: allTopics = [], isLoading } = useQuery({
    queryKey: ['all-topics'],
    queryFn: fetchAllTopics,
    staleTime: 5 * 60 * 1000,
  });

  // topics grouped by course id.
  const topicsByCourse = useMemo(() => {
    const map = new Map();
    for (const t of allTopics) {
      if (!map.has(t.course_id)) map.set(t.course_id, []);
      map.get(t.course_id).push(t);
    }
    return map;
  }, [allTopics]);

  const query = search.trim().toLowerCase();
  const searching = query.length > 0;

  const toggleCourse = (courseId) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(courseId)) next.delete(courseId);
      else next.add(courseId);
      return next;
    });

  // When searching, show courses with a name match (all their topics) or a topic
  // match (just the matching topics). Otherwise show every course.
  const rows = courses
    .map((course) => {
      const topics = topicsByCourse.get(course.id) ?? [];
      if (!searching) return { course, topics };
      const nameMatch = course.course_name.toLowerCase().includes(query);
      const visible = nameMatch
        ? topics
        : topics.filter((t) => t.topic_name.toLowerCase().includes(query));
      return { course, topics: visible };
    })
    .filter((r) => (searching ? r.topics.length > 0 : true));

  const selectedCount = (course) =>
    (topicsByCourse.get(course.id) ?? []).filter((t) => selected[t.id] != null).length;

  return (
    <div className="atp">
      <input
        type="search"
        className="atp-search"
        placeholder="Search courses and topics…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        aria-label="Search courses and topics"
      />
      {coursesError && <p className="teacher-error">Error: {coursesError.message}</p>}
      {isLoading && <p>Loading topics…</p>}
      {searching && !isLoading && rows.length === 0 && (
        <p className="teacher-empty">No courses or topics match “{search.trim()}”.</p>
      )}

      {rows.map(({ course, topics }) => {
        const isOpen = searching || expanded.has(course.id);
        const n = selectedCount(course);
        return (
          <div key={course.id} className={`atp-course${isOpen ? ' open' : ''}`}>
            <button type="button" className="atp-course-header" onClick={() => toggleCourse(course.id)}>
              <span className="atp-course-name">{course.course_name}</span>
              <span className="atp-course-right">
                {n > 0 && <span className="atp-course-count">{n} selected</span>}
                <svg className="atp-chevron" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </span>
            </button>
            {isOpen && (
              <div className="atp-topics">
                {groupByUnit(topics).map((group) => (
                  <div className="atp-unit" key={group.key}>
                    {group.name && <h4 className="atp-unit-title">{group.name}</h4>}
                    <ul>
                      {group.topics.map((t) => {
                        const isSelected = selected[t.id] != null;
                        return (
                          <li key={t.id}>
                            <span className="atp-topic-name">{t.topic_name}</span>
                            <input
                              type="checkbox"
                              className="atp-topic-checkbox"
                              checked={isSelected}
                              onChange={() => onToggleTopic(t.id)}
                              aria-label={t.topic_name}
                            />
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export default AssignmentTopicPicker;
