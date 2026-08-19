import { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import CourseBar from './CourseBar.jsx';
import { apiFetch, localDay } from './auth.js';
import { createLogger } from './logger.js';
import './CourseList.css';

const log = createLogger('courses');

async function fetchCourses() {
  const response = await apiFetch(`/courses/`);
  if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
  const result = await response.json();
  log.debug(`Loaded ${result.courses.length} courses`);
  return result.courses;
}

// Every topic across every course. Fetched only once the user starts searching
// (see the `enabled` flag below), since search must match topic names even for
// courses the user hasn't expanded — and so hasn't lazily loaded topics for.
async function fetchAllTopics() {
  const response = await apiFetch(`/topics/`);
  if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
  const result = await response.json();
  return result.topics;
}

function CourseList() {
  const queryClient = useQueryClient();
  const [expandedCourses, setExpandedCourses] = useState(new Set());
  const [topicsMap, setTopicsMap] = useState({});
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');

  const query = search.trim().toLowerCase();
  const searching = query.length > 0;

  const { data: courses = [], error: coursesError } = useQuery({
    queryKey: ['courses'],
    queryFn: fetchCourses,
  });

  const { data: allTopics } = useQuery({
    queryKey: ['all-topics'],
    queryFn: fetchAllTopics,
    enabled: searching,
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

  // Optimistically flip a course's selection state in the cached courses list.
  const patchCourseSelected = (courseID, isSelected, isPartial) =>
    queryClient.setQueryData(['courses'], (prev = []) =>
      prev.map(c => c.id === courseID ? { ...c, is_selected: isSelected, is_partial: isPartial } : c));

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
      const updatedTopics = topicsMap[courseID].map(t => t.id === topicID ? { ...t, is_selected: newValue } : t);
      const allSelected = updatedTopics.every(t => t.is_selected);
      const anySelected = updatedTopics.some(t => t.is_selected);
      setTopicsMap(prev => ({ ...prev, [courseID]: updatedTopics }));
      patchCourseSelected(courseID, allSelected, anySelected && !allSelected);
    } catch (err) {
      log.error(`Failed to toggle topic ${topicID}:`, err.message);
      setError(err.message);
    }
  };

  const handleCourseToggle = async (courseID, newValue) => {
    try {
      const response = await apiFetch(`/courses/${courseID}/select?today=${localDay()}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_selected: newValue }),
      });
      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
      log.info(`Course ${courseID} ${newValue ? 'selected' : 'deselected'}`);
      // Selecting/deselecting a whole course leaves no topics in a mixed state.
      patchCourseSelected(courseID, newValue, false);
      if (topicsMap[courseID]) {
        setTopicsMap(prev => ({
          ...prev,
          [courseID]: prev[courseID].map(t => ({ ...t, is_selected: newValue })),
        }));
      }
    } catch (err) {
      log.error(`Failed to toggle course ${courseID}:`, err.message);
      setError(err.message);
    }
  };

  // Build the list to render. When searching, keep only courses that match by
  // name (show all their topics) or that contain a matching topic (show just
  // those), and force them open so the matches are visible. topicsMap still
  // holds each course's full topic list — we filter only what's displayed, so
  // the selection handlers keep computing course state over every topic.
  const rows = searching
    ? courses
        .map((course) => {
          const nameMatch = course.course_name.toLowerCase().includes(query);
          const topics = topicsMap[course.id] ?? [];
          const visibleTopics = nameMatch
            ? topics
            : topics.filter((t) => t.topic_name.toLowerCase().includes(query));
          return { course, visibleTopics, matched: nameMatch || visibleTopics.length > 0 };
        })
        .filter((r) => r.matched)
    : courses.map((course) => ({
        course,
        visibleTopics: topicsMap[course.id] ?? [],
        matched: true,
      }));

  return (
    <div className="course-list">
      <div className="course-list-intro">
        <h1 className="course-list-title">Choose what to review</h1>
        <p className="course-list-subtitle">
          Select the courses and topics that you would like to review.
          Selecting a course selects all of the topics within it.
        </p>
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
      {searching && rows.length === 0 && (
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
          isCourseSelected={course.is_selected}
          isCoursePartial={course.is_partial}
          onItemClick={handleCourseBarClick}
          onTopicToggle={handleTopicToggle}
          onCourseToggle={handleCourseToggle}
        />
      ))}
    </div>
  );
}

export default CourseList;
