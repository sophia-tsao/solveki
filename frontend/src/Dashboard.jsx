import { useQuery } from '@tanstack/react-query';
import './Dashboard.css';
import Calendar from './Calendar.jsx';
import TopicProgress from './TopicProgress.jsx';
import { apiFetch, localDay } from './auth.js';
import { createLogger } from './logger.js';

const log = createLogger('dashboard');

async function fetchDashboard() {
  const response = await apiFetch(`/dashboard/?today=${localDay()}`);
  if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
  const result = await response.json();
  log.debug(`Loaded ${result.selected.length} selected, ${result.upcoming.length} upcoming`);
  return result;
}

function Dashboard() {
  const { data, error } = useQuery({
    queryKey: ['dashboard', localDay()],
    queryFn: fetchDashboard,
  });
  const selected = data?.selected ?? [];
  const upcoming = data?.upcoming ?? [];

  return (
    <div className="dashboard">
      <header className="dash-intro">
        <h1 className="dash-title">Your progress</h1>
        <p className="dash-subtitle">
          A snapshot of everything you're reviewing — each topic grouped by how
          well you know it, plus your overall mix and practice history.
        </p>
      </header>

      {error && <p className="dash-error">Error: {error.message}</p>}

      <TopicProgress selected={selected} upcoming={upcoming} calendar={<Calendar />} />
    </div>
  );
}

export default Dashboard;
