import './Teacher.css';

// The four proficiency bands, in progression order, on the teacher pages' single
// blue ramp (light → dark), so a level never borrows a status color (red means
// overdue, amber needs help). Mirrors the --b-* tokens in tokens.css; hex here
// because SVG fill attributes can't read CSS variables. `ink` is the text color
// that reads on the band. Student pages keep TopicProgress's colorful palette.
export const BANDS = [
  { key: 'new', label: 'New', color: '#86b6ef', ink: '#0d366b' },
  { key: 'learning', label: 'Learning', color: '#3987e5', ink: '#ffffff' },
  { key: 'familiar', label: 'Familiar', color: '#1c5cab', ink: '#ffffff' },
  { key: 'proficient', label: 'Proficient', color: '#0d366b', ink: '#ffffff' },
];

// No data yet (a topic the student hasn't started).
export const BAND_NONE = { key: 'none', label: 'Not started', color: '#eef2f7', ink: '#94a3b8' };

// Segments narrower than this share of the bar are too thin to fit their label.
const MIN_LABEL_PCT = 6;

// A thin stacked bar of a band-count map, e.g. {new, learning, familiar, proficient}.
// `showPercents` writes each band's share inside its segment, at the same size.
export function BandBar({ counts, showPercents = false }) {
  const total = BANDS.reduce((sum, b) => sum + (counts[b.key] || 0), 0);
  if (total === 0) return <span className="teacher-card-stat">—</span>;
  const pct = (b) => Math.round(((counts[b.key] || 0) / total) * 100);
  const label = showPercents
    ? BANDS.map((b) => `${b.label}: ${pct(b)}%`).join(', ')
    : BANDS.map((b) => `${b.label}: ${counts[b.key] || 0}`).join(', ');
  return (
    <span className="ad-bandbar" role="img" aria-label={label}>
      {BANDS.map((b) => {
        const n = counts[b.key] || 0;
        if (n === 0) return null;
        return (
          <span key={b.key} className="ad-bandbar-seg" style={{ flexGrow: n, background: b.color }}>
            {showPercents && pct(b) >= MIN_LABEL_PCT && (
              <span className="ad-bandbar-pct" aria-hidden="true" style={{ color: b.ink }}>{pct(b)}%</span>
            )}
          </span>
        );
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
