import './Teacher.css';

// "Struggled with most": the topics with the lowest first-try accuracy, as
// ranked by the backend (`struggled_topics`). `showStudents` adds how many
// students missed each one, for reports spanning a group of students.
function StruggledTopics({ topics, showStudents = false, emptyText }) {
  return (
    <div className="teacher-card static struggled-card">
      <div className="teacher-card-title">Struggled with most</div>
      {topics.length === 0 ? (
        <p className="teacher-card-stat">{emptyText}</p>
      ) : (
        <ol className="struggled-list">
          {topics.map((t) => (
            <li key={t.topic_id}>
              <span className="struggled-name">{t.topic_name}</span>
              <span className="teacher-card-stat">
                {t.accuracy}% right first try · {t.answers} answer{t.answers === 1 ? '' : 's'}
                {showStudents && ` · ${t.students} student${t.students === 1 ? '' : 's'} missed it`}
              </span>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

export default StruggledTopics;
