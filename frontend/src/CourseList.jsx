import { useState } from 'react';
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

function CourseList() {
  const queryClient = useQueryClient();
  const [expandedCourses, setExpandedCourses] = useState(new Set());
  const [topicsMap, setTopicsMap] = useState({});
  const [error, setError] = useState(null);

  const { data: courses = [], error: coursesError } = useQuery({
    queryKey: ['courses'],
    queryFn: fetchCourses,
  });

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

  return (
    <div className="course-list">
      <div className="course-list-intro">
        <h1 className="course-list-title">Choose what to review</h1>
        <p className="course-list-subtitle">
          Select the courses and topics that you would like to review.
          Selecting a course selects all of the topics within it.
        </p>
      </div>
      {(error || coursesError) && (
        <p className="course-list-error">Error: {error || coursesError.message}</p>
      )}
      {courses.map((course) => (
        <CourseBar
          key={course.id}
          id={course.id}
          courseName={course.course_name}
          gradeLevel={course.grade_level}
          topics={topicsMap[course.id] ?? []}
          isOpen={expandedCourses.has(course.id)}
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
