import { useState, useEffect } from 'react';
import CourseBar from './CourseBar.jsx';
import { apiFetch, localDay } from './auth.js';
import { createLogger } from './logger.js';

const log = createLogger('courses');

function CourseList() {
  const [courses, setCourses] = useState([]);
  const [expandedCourses, setExpandedCourses] = useState(new Set());
  const [topicsMap, setTopicsMap] = useState({});
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const response = await apiFetch(`/courses/`);
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        const result = await response.json();
        log.debug(`Loaded ${result.courses.length} courses`);
        setCourses(result.courses);
      } catch (err) {
        log.error('Failed to load courses:', err.message);
        setError(err.message);
      }
    };
    fetchCourses();
  }, []);

  const handleCourseBarClick = async (courseID) => {
    if (expandedCourses.has(courseID)) {
      setExpandedCourses(prev => { const next = new Set(prev); next.delete(courseID); return next; });
      return;
    }
    if (!topicsMap[courseID]) {
      try {
        const response = await apiFetch(`/courses/${courseID}/topics`);
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        const result = await response.json();
        setTopicsMap(prev => ({ ...prev, [courseID]: result.topics }));
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
      setTopicsMap(prev => ({ ...prev, [courseID]: updatedTopics }));
      setCourses(prev => prev.map(c => c.id === courseID ? { ...c, is_selected: allSelected } : c));
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
      setCourses(prev => prev.map(c => c.id === courseID ? { ...c, is_selected: newValue } : c));
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
    <div>
      {error && <p>Error: {error}</p>}
      {courses.map((course) => (
        <CourseBar
          key={course.id}
          id={course.id}
          courseName={course.course_name}
          gradeLevel={course.grade_level}
          topics={topicsMap[course.id] ?? []}
          isOpen={expandedCourses.has(course.id)}
          isCourseSelected={course.is_selected}
          onItemClick={handleCourseBarClick}
          onTopicToggle={handleTopicToggle}
          onCourseToggle={handleCourseToggle}
        />
      ))}
    </div>
  );
}

export default CourseList;
