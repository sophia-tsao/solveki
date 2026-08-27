import { useState, useEffect, useRef, useLayoutEffect } from 'react';
import './CourseBar.css';

function CourseBar(props) {
  const [displayedTopics, setDisplayedTopics] = useState(props.topics);
  const topicsInnerRef = useRef(null);
  const [topicsHeight, setTopicsHeight] = useState(0);
  const checkboxRef = useRef(null);

  // `indeterminate` (the checkbox's dash) is a DOM-only property with no React
  // attribute, so drive it imperatively. It shows only when some — but not
  // all — of the course's topics are selected.
  const isPartial = !props.isCourseSelected && !!props.isCoursePartial;
  useEffect(() => {
    if (checkboxRef.current) checkboxRef.current.indeterminate = isPartial;
  }, [isPartial]);

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

  // Group topics under their unit, preserving the backend's curriculum-unit
  // order. Topics with no unit (outside the taxonomy) collect under a null
  // group rendered without a heading.
  const unitGroups = [];
  const groupIndex = new Map();
  for (const topic of displayedTopics) {
    const key = topic.unit_key ?? '__none__';
    let group = groupIndex.get(key);
    if (!group) {
      group = { key, name: topic.unit_name || null, topics: [] };
      groupIndex.set(key, group);
      unitGroups.push(group);
    }
    group.topics.push(topic);
  }

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
            ref={checkboxRef}
            type="checkbox"
            className={`course-bar-checkbox${isPartial ? ' partial' : ''}`}
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
          {unitGroups.map((group) => (
            <div className="course-bar-unit" key={group.key}>
              {group.name && (
                <h3 className="course-bar-unit-title">{group.name}</h3>
              )}
              <ul>
                {group.topics.map((topic) => (
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
          ))}
        </div>
      </div>
    </div>
  );
}

export default CourseBar;
