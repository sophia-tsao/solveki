import { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import CourseBar from './CourseBar.jsx';
import { apiFetch, localDay } from './auth.js';
import { readDiagnostic } from './diagnosticStore.js';
import { createLogger } from './logger.js';
import './CourseList.css';

// Entry-button copy depends on whether the user has a diagnostic in flight or
// already finished one. Read at render (cheap); CourseList remounts on every
// navigation back to this page, so the label is always current.
function diagnosticButtonLabel(userId) {
  const status = readDiagnostic(userId)?.status;
  if (status === 'in_progress') return 'Resume diagnostic';
  if (status === 'completed') return 'Retake diagnostic';
  return 'Not sure where to start? Take the 5-question diagnostic';
}

const log = createLogger('courses');

async function fetchCourses() {
  const response = await apiFetch(`/courses/`);
  if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
  const result = await response.json();
  log.debug(`Loaded ${result.courses.length} courses`);
  return result.courses;
}

// Every topic across every course. Prefetched on mount so the first search is
// instant — search must match topic names even for courses the user hasn't
// expanded (and so hasn't lazily loaded topics for), and waiting until the first
// keystroke to fetch would stall that first search on a full network round-trip.
async function fetchAllTopics() {
  const response = await apiFetch(`/topics/`);
  if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
  const result = await response.json();
  return result.topics;
}

function CourseList({ onStartDiagnostic, userId }) {
  const queryClient = useQueryClient();
  const [expandedCourses, setExpandedCourses] = useState(new Set());
  const [topicsMap, setTopicsMap] = useState({});
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  // Keys of controls with a selection request in flight (`course:<id>` /
  // `topic:<id>`). Drives the disabled state so a control can't be re-clicked
  // mid-request, and lets the handlers ignore a repeat click outright.
  const [pending, setPending] = useState(() => new Set());
  const setPendingKey = (key, on) =>
    setPending((prev) => {
      const next = new Set(prev);
      if (on) next.add(key);
      else next.delete(key);
      return next;
    });

  const query = search.trim().toLowerCase();
  const searching = query.length > 0;

  const { data: courses = [], error: coursesError } = useQuery({
    queryKey: ['courses'],
    queryFn: fetchCourses,
  });

  const { data: allTopics, isLoading: topicsLoading } = useQuery({
    queryKey: ['all-topics'],
    queryFn: fetchAllTopics,
    staleTime: 5 * 60 * 1000,
  });

  // Once the full topic list arrives, seed topicsMap for any course we haven't
  // loaded topics for yet. We never overwrite an existing entry: a lazily-loaded
  // (or optimistically-toggled) course already holds the authoritative state.
  useEffect(() => {
    if (!allTopics) return;
    setTopicsMap((prev) => {
      const next = { ...prev };
      for (const topic of allTopics) {
        if (!next[topic.course_id]) next[topic.course_id] = [];
      }
      for (const topic of allTopics) {
        if (prev[topic.course_id]) continue; // keep already-loaded courses intact
        next[topic.course_id].push(topic);
      }
      return next;
    });
  }, [allTopics]);

  // Optimistically set a course's tri-state topic-selection status
  // ('all' | 'partial' | 'none') in the cached courses list.
  const patchCourseSelection = (courseID, status) =>
    queryClient.setQueryData(['courses'], (prev = []) =>
      prev.map(c => c.id === courseID ? { ...c, topic_selection_status: status } : c));

  // Derive a course's header status from its topics' selection statuses.
  const selectionStatusFromTopics = (topics) => {
    if (topics.length && topics.every(t => t.selection_status === 'selected')) return 'all';
    if (topics.some(t => t.selection_status === 'selected')) return 'partial';
    return 'none';
  };

  const applyCourseStateFromTopics = (courseID, topics) =>
    patchCourseSelection(courseID, selectionStatusFromTopics(topics));

  const handleCourseBarClick = async (courseID) => {
    if (expandedCourses.has(courseID)) {
      setExpandedCourses(prev => { const next = new Set(prev); next.delete(courseID); return next; });
      return;
    }
    if (!topicsMap[courseID]) {
      try {
        // fetchQuery caches by key and de-duplicates in-flight requests, so
        // re-expanding a course (or racing double-clicks) won't re-hit the API.
        const topics = await queryClient.fetchQuery({
          queryKey: ['topics', courseID],
          queryFn: async () => {
            const response = await apiFetch(`/courses/${courseID}/topics`);
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            const result = await response.json();
            return result.topics;
          },
        });
        setTopicsMap(prev => ({ ...prev, [courseID]: topics }));
      } catch (err) {
        log.error(`Failed to load topics for course ${courseID}:`, err.message);
        setError(err.message);
        return;
      }
    }
    setExpandedCourses(prev => new Set([...prev, courseID]));
  };

  const handleTopicToggle = async (courseID, topicID, newValue) => {
    const key = `topic:${topicID}`;
    if (pending.has(key)) return; // a request is already in flight for this topic
    // Flip the UI *before* the request (true optimistic update) so the checkbox
    // reacts instantly; a slow round-trip no longer looks like a dead click and
    // invites a duplicate. Snapshot the prior state to roll back on failure.
    const prevTopics = topicsMap[courseID];
    const updatedTopics = prevTopics.map(t =>
      t.id === topicID ? { ...t, selection_status: newValue ? 'selected' : 'unselected' } : t);
    setTopicsMap(prev => ({ ...prev, [courseID]: updatedTopics }));
    applyCourseStateFromTopics(courseID, updatedTopics);
    setPendingKey(key, true);
    try {
      // Send today so the deck-tail regeneration this triggers targets the
      // user's local day, matching the deck the practice page shows.
      const response = await apiFetch(`/topics/${topicID}/select?today=${localDay()}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_selected: newValue }),
      });
      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
      log.info(`Topic ${topicID} ${newValue ? 'selected' : 'deselected'}`);
    } catch (err) {
      setTopicsMap(prev => ({ ...prev, [courseID]: prevTopics })); // roll back
      applyCourseStateFromTopics(courseID, prevTopics);
      log.error(`Failed to toggle topic ${topicID}:`, err.message);
      setError(err.message);
    } finally {
      setPendingKey(key, false);
    }
  };

  const handleCourseToggle = async (courseID, newValue) => {
    const key = `course:${courseID}`;
    if (pending.has(key)) return; // a request is already in flight for this course
    // Optimistically flip the course header and all its loaded topics. Snapshot
    // the prior header state (from the courses cache) to restore on failure.
    const prevCourse = courses.find(c => c.id === courseID);
    const prevTopics = topicsMap[courseID];
    patchCourseSelection(courseID, newValue ? 'all' : 'none'); // whole-course toggle -> no mixed state
    if (prevTopics) {
      setTopicsMap(prev => ({
        ...prev,
        [courseID]: prevTopics.map(t => ({ ...t, selection_status: newValue ? 'selected' : 'unselected' })),
      }));
    }
    setPendingKey(key, true);
    try {
      const response = await apiFetch(`/courses/${courseID}/select?today=${localDay()}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_selected: newValue }),
      });
      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
      log.info(`Course ${courseID} ${newValue ? 'selected' : 'deselected'}`);
    } catch (err) {
      if (prevCourse) patchCourseSelection(courseID, prevCourse.topic_selection_status);
      if (prevTopics) setTopicsMap(prev => ({ ...prev, [courseID]: prevTopics })); // roll back
      log.error(`Failed to toggle course ${courseID}:`, err.message);
      setError(err.message);
    } finally {
      setPendingKey(key, false);
    }
  };

  // Build the list to render. When searching, keep only courses that have at
  // least one topic to show: a name match surfaces all the course's topics, a
  // topic match surfaces just the matching ones. Requiring a visible topic
  // means we never force open an empty course box — including while the full
  // topic list is still loading (topicsMap not yet seeded). topicsMap still
  // holds each course's full topic list, so the selection handlers keep
  // computing course state over every topic, not just the visible subset.
  const rows = searching
    ? courses
        .map((course) => {
          const nameMatch = course.course_name.toLowerCase().includes(query);
          const topics = topicsMap[course.id] ?? [];
          const visibleTopics = nameMatch
            ? topics
            : topics.filter((t) => t.topic_name.toLowerCase().includes(query));
          return { course, visibleTopics };
        })
        .filter((r) => r.visibleTopics.length > 0)
    : courses.map((course) => ({
        course,
        visibleTopics: topicsMap[course.id] ?? [],
      }));

  return (
    <div className="course-list">
      <div className="course-list-intro">
        <h1 className="course-list-title">Choose what to review</h1>
        <p className="course-list-subtitle">
          Select the courses and topics that you would like to review.
          Selecting a course selects all of the topics within it.
        </p>
        {onStartDiagnostic && (
          <button className="course-list-diagnostic" onClick={onStartDiagnostic}>
            {diagnosticButtonLabel(userId)}
          </button>
        )}
      </div>
      <div className="course-search">
        <input
          type="search"
          className="course-search-input"
          placeholder="Search courses and topics…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Search courses and topics"
        />
      </div>
      {(error || coursesError) && (
        <p className="course-list-error">Error: {error || coursesError.message}</p>
      )}
      {searching && topicsLoading && rows.length === 0 && (
        <p className="course-list-empty">Searching…</p>
      )}
      {searching && !topicsLoading && rows.length === 0 && (
        <p className="course-list-empty">No courses or topics match “{search.trim()}”.</p>
      )}
      {rows.map(({ course, visibleTopics }) => (
        <CourseBar
          key={course.id}
          id={course.id}
          courseName={course.course_name}
          gradeLevel={course.grade_level}
          topics={visibleTopics}
          isOpen={searching || expandedCourses.has(course.id)}
          courseSelection={course.topic_selection_status}
          onItemClick={handleCourseBarClick}
          onTopicToggle={handleTopicToggle}
          onCourseToggle={handleCourseToggle}
          isCoursePending={pending.has(`course:${course.id}`)}
          isTopicPending={(topicID) => pending.has(`topic:${topicID}`)}
        />
      ))}
    </div>
  );
}

export default CourseList;
