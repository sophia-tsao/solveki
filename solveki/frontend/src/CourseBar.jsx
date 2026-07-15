import { useState, useEffect } from 'react';
import './CourseBar.css';

function CourseBar(props) {
  const [displayedTopics, setDisplayedTopics] = useState(props.topics);

  useEffect(() => {
    if (props.topics.length > 0) {
      setDisplayedTopics(props.topics);
    }
  }, [props.topics]);

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

      <div className="course-bar-topics">
        <div className="course-bar-topics-inner">
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
