import { LEVEL_COLOR } from './TopicProgress.jsx';
import './Teacher.css';

// The four proficiency bands, in progression order, sharing the dashboard's
// color system (`young`/`mature` are its internal keys for Familiar/Proficient).
export const BANDS = [
  { key: 'new', label: 'New', color: LEVEL_COLOR.new },
  { key: 'learning', label: 'Learning', color: LEVEL_COLOR.learning },
  { key: 'familiar', label: 'Familiar', color: LEVEL_COLOR.young },
  { key: 'proficient', label: 'Proficient', color: LEVEL_COLOR.mature },
];

// A thin stacked bar of a band-count map, e.g. {new, learning, familiar, proficient}.
export function BandBar({ counts }) {
  const total = BANDS.reduce((sum, b) => sum + (counts[b.key] || 0), 0);
  if (total === 0) return <span className="teacher-card-stat">—</span>;
  return (
    <span className="ad-bandbar" role="img" aria-label={BANDS.map((b) => `${b.label}: ${counts[b.key] || 0}`).join(', ')}>
      {BANDS.map((b) => {
        const n = counts[b.key] || 0;
        if (n === 0) return null;
        return <span key={b.key} className="ad-bandbar-seg" style={{ flexGrow: n, background: b.color }} />;
      })}
    </span>
  );
}

// The band color key, optionally with each band's count.
export function BandLegend({ counts }) {
  return (
    <ul className="ad-legend">
      {BANDS.map((b) => (
        <li key={b.key}>
          <span className="ad-swatch" style={{ background: b.color }} />
          {b.label}{counts && <> <strong>{counts[b.key] || 0}</strong></>}
        </li>
      ))}
    </ul>
  );
}
