import { useState, useEffect } from 'react';
import CourseBar from './CourseBar.jsx';

function CourseList() {
  const [courses, setCourses] = useState([]);
  const [expandedCourses, setExpandedCourses] = useState(new Set());
  const [topicsMap, setTopicsMap] = useState({});
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/courses/`);
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        const result = await response.json();
        setCourses(result.courses);
      } catch (err) {
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
        const response = await fetch(`${import.meta.env.VITE_API_URL}/courses/${courseID}/topics`);
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        const result = await response.json();
        setTopicsMap(prev => ({ ...prev, [courseID]: result.topics }));
      } catch (err) {
        setError(err.message);
        return;
      }
    }
    setExpandedCourses(prev => new Set([...prev, courseID]));
  };

  const handleTopicToggle = async (courseID, topicID, newValue) => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/topics/${topicID}/select`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_selected: newValue }),
      });
      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
      setTopicsMap(prev => ({
        ...prev,
        [courseID]: prev[courseID].map(t => t.id === topicID ? { ...t, is_selected: newValue } : t),
      }));
    } catch (err) {
      setError(err.message);
    }
  };

  const handleCourseToggle = async (courseID, newValue) => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/courses/${courseID}/select`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_selected: newValue }),
      });
      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
      if (topicsMap[courseID]) {
        setTopicsMap(prev => ({
          ...prev,
          [courseID]: prev[courseID].map(t => ({ ...t, is_selected: newValue })),
        }));
      }
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div>
      {error && <p>Error: {error}</p>}
      {courses.map((course) => {
        const topics = topicsMap[course.id] ?? [];
        const isExpanded = expandedCourses.has(course.id);
        const allSelected = topics.length > 0 && topics.every(t => t.is_selected);
        return (
          <CourseBar
            key={course.id}
            id={course.id}
            courseName={course.course_name}
            gradeLevel={course.grade_level}
            topics={topics}
            isOpen={isExpanded}
            isCourseSelected={allSelected}
            onItemClick={handleCourseBarClick}
            onTopicToggle={handleTopicToggle}
            onCourseToggle={handleCourseToggle}
          />
        );
      })}
    </div>
  );
}

export default CourseList;
