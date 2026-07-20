import { useState, useEffect, useRef, useLayoutEffect } from 'react';
import './CourseBar.css';

function CourseBar(props) {
  const [displayedTopics, setDisplayedTopics] = useState(props.topics);
  const topicsInnerRef = useRef(null);
  const [topicsHeight, setTopicsHeight] = useState(0);

  useEffect(() => {
    if (props.topics.length > 0) {
      setDisplayedTopics(props.topics);
    }
  }, [props.topics]);

  // Drive the expand/collapse height from the actual content so every topic
  // is visible no matter how many there are (a fixed max-height clips long
  // lists). Re-measure whenever the open state or topics change.
  useLayoutEffect(() => {
    if (topicsInnerRef.current) {
      setTopicsHeight(topicsInnerRef.current.scrollHeight);
    }
  }, [props.isOpen, displayedTopics]);

  const handleCourseCheckbox = (e) => {
    e.stopPropagation();
    props.onCourseToggle(props.id, e.target.checked);
  };

  const handleTopicCheckbox = (e, topicID) => {
    e.stopPropagation();
    props.onTopicToggle(props.id, topicID, e.target.checked);
  };

  return (
    <div
      className={`course-bar${props.isOpen ? ' open' : ''}`}
      onClick={() => props.onItemClick(props.id)}
    >
      <div className="course-bar-header">
        <div className="course-bar-info">
          <span className="course-bar-name">{props.courseName}</span>
          <span className="course-bar-grade">Grade {props.gradeLevel}</span>
        </div>
        <div className="course-bar-header-right">
          <input
            type="checkbox"
            className="course-bar-checkbox"
            checked={props.isCourseSelected}
            onChange={handleCourseCheckbox}
            onClick={(e) => e.stopPropagation()}
          />
          <svg className="course-bar-chevron" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </div>
      </div>

      <div
        className="course-bar-topics"
        style={{ maxHeight: props.isOpen ? topicsHeight : 0 }}
      >
        <div className="course-bar-topics-inner" ref={topicsInnerRef}>
          <ul>
            {displayedTopics.map((topic) => (
              <li key={topic.id}>
                <span className="topic-name">{topic.topic_name}</span>
                <input
                  type="checkbox"
                  className="topic-checkbox"
                  checked={topic.is_selected}
                  onChange={(e) => handleTopicCheckbox(e, topic.id)}
                  onClick={(e) => e.stopPropagation()}
                />
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default CourseBar;
