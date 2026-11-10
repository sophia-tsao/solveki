import '../Teacher.css';

// A row of tabs. `tabs` is a list of { key, label, count? }; the parent owns the
// selected key and renders the matching panel itself.
function Tabs({ tabs, value, onChange, label }) {
  return (
    <div className="teacher-tabs" role="tablist" aria-label={label}>
      {tabs.map((t) => (
        <button
          key={t.key}
          type="button"
          role="tab"
          className="teacher-tab"
          aria-selected={value === t.key}
          onClick={() => onChange(t.key)}
        >
          {t.label}
          {t.count != null && <span className="teacher-tab-count">{t.count}</span>}
        </button>
      ))}
    </div>
  );
}

export default Tabs;
