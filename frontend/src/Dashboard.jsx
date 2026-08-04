import { useState, useEffect } from 'react';
import './Dashboard.css';
import { apiFetch, localDay } from './auth.js';
import { createLogger } from './logger.js';

const log = createLogger('dashboard');

// Bucket a topic's interval (days until next review) into a status color.
// Short intervals mean the topic is still being learned / seen often (red);
// long intervals mean it's well-retained and rests longer between reviews
// (green). The circle next to each number carries this at a glance.
function intervalLevel(interval) {
  if (interval <= 1) return 'new';
  if (interval < 6) return 'learning';
  if (interval < 21) return 'young';
  return 'mature';
}

// Ease is the SM-2 multiplier (floor 1.3, starts 2.5). Lower ease means the
// topic keeps coming up hard, so its intervals grow slowly — worth flagging.
function easeLevel(ease) {
  if (ease < 1.6) return 'new';
  if (ease < 2.2) return 'learning';
  if (ease < 2.6) return 'young';
  return 'mature';
}

function Stat({ label, value, level }) {
  return (
    <div className="dash-stat">
      <span className="dash-stat-label">{label}</span>
      <span className="dash-stat-value">
        <span className={`dash-dot dash-dot-${level}`} />
        {value}
      </span>
    </div>
  );
}

function TopicCard({ topic }) {
  return (
    <div className="dash-card">
      <div className="dash-card-head">
        <span className="dash-card-name">{topic.topic_name}</span>
        {topic.course_name && (
          <span className="dash-card-course">{topic.course_name}</span>
        )}
      </div>
      <div className="dash-card-stats">
        <Stat
          label="Repetitions"
          value={topic.repetitions}
          level={intervalLevel(topic.interval)}
        />
        <Stat
          label="Ease"
          value={topic.ease.toFixed(2)}
          level={easeLevel(topic.ease)}
        />
        <Stat
          label="Interval"
          value={topic.interval === 1 ? '1 day' : `${topic.interval} days`}
          level={intervalLevel(topic.interval)}
        />
      </div>
    </div>
  );
}

function Section({ title, subtitle, topics }) {
  return (
    <section className="dash-section">
      <h2 className="dash-section-title">{title}</h2>
      <p className="dash-section-subtitle">{subtitle}</p>
      {topics.length === 0 ? (
        <p className="dash-empty">No topics yet.</p>
      ) : (
        <div className="dash-cards">
          {topics.map((t) => <TopicCard key={t.id} topic={t} />)}
        </div>
      )}
    </section>
  );
}

function Dashboard() {
  const [selected, setSelected] = useState([]);
  const [upcoming, setUpcoming] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await apiFetch(`/dashboard/?today=${localDay()}`);
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        const result = await response.json();
        log.debug(`Loaded ${result.selected.length} selected, ${result.upcoming.length} upcoming`);
        setSelected(result.selected);
        setUpcoming(result.upcoming);
      } catch (err) {
        log.error('Failed to load dashboard:', err.message);
        setError(err.message);
      }
    };
    fetchDashboard();
  }, []);

  return (
    <div className="dashboard">
      {error && <p className="dash-error">Error: {error}</p>}
      <Section
        title="Selected topics"
        subtitle="Every topic you've selected, most due first."
        topics={selected}
      />
      <Section
        title="Shown soon"
        subtitle="The topics your next practice session will draw from."
        topics={upcoming}
      />
    </div>
  );
}

export default Dashboard;
