import { useEffect, useId, useRef, useState } from 'react';
import '../Teacher.css';

// A "⋯" button that opens a small menu of secondary actions. `items` is a list
// of { label, onSelect, danger? }. Closes on selection, outside click or Escape.
function OverflowMenu({ items, label = 'More actions', trigger = '⋯', triggerClassName = 'teacher-button ghost' }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);
  const menuId = useId();

  useEffect(() => {
    if (!open) return undefined;
    const onDown = (e) => {
      if (rootRef.current && !rootRef.current.contains(e.target)) setOpen(false);
    };
    const onKey = (e) => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  return (
    <span className="overflow-menu" ref={rootRef} onClick={(e) => e.stopPropagation()}>
      <button
        type="button"
        className={triggerClassName}
        aria-label={label}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={open ? menuId : undefined}
        onClick={() => setOpen((v) => !v)}
      >
        {trigger}
      </button>
      {open && (
        <ul className="overflow-menu-list" role="menu" id={menuId}>
          {items.map((item) => (
            <li key={item.label} role="none">
              <button
                type="button"
                role="menuitem"
                className={`overflow-menu-item${item.danger ? ' danger' : ''}`}
                onClick={() => {
                  setOpen(false);
                  item.onSelect();
                }}
              >
                {item.label}
              </button>
            </li>
          ))}
        </ul>
      )}
    </span>
  );
}

export default OverflowMenu;
