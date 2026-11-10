import '../Teacher.css';

// The top of a teacher page: breadcrumbs, title, a muted subtitle, and the
// page's actions on the right. `crumbs` is a list of { label, onClick? }; the
// last crumb is the current page and isn't a link.
function PageHeader({ crumbs, title, sub, actions, leading }) {
  return (
    <>
      {crumbs && crumbs.length > 0 && (
        <nav aria-label="Breadcrumb">
          <ol className="page-crumbs">
            {crumbs.map((c, i) => (
              <li key={`${c.label}-${i}`}>
                {c.onClick && i < crumbs.length - 1 ? (
                  <button type="button" onClick={c.onClick}>{c.label}</button>
                ) : (
                  <span aria-current={i === crumbs.length - 1 ? 'page' : undefined}>{c.label}</span>
                )}
              </li>
            ))}
          </ol>
        </nav>
      )}
      <div className="page-header">
        {leading}
        <div className="page-header-text">
          <h1>{title}</h1>
          {sub && <div className="page-header-sub">{sub}</div>}
        </div>
        {actions && <div className="page-header-actions">{actions}</div>}
      </div>
    </>
  );
}

export default PageHeader;
