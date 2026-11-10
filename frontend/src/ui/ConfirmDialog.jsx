import { useEffect, useId, useRef } from 'react';
import '../Teacher.css';

// A modal confirmation for destructive actions, on the native <dialog> so focus
// trapping and Escape-to-cancel come for free. Rendered only while `open`.
function ConfirmDialog({ open, title, body, confirmLabel = 'Delete', onConfirm, onCancel, busy = false }) {
  const ref = useRef(null);
  const titleId = useId();

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      // jsdom has no showModal; fall back to the open attribute there.
      if (dialog.showModal) dialog.showModal();
      else dialog.setAttribute('open', '');
    } else if (!open && dialog.open) {
      if (dialog.close) dialog.close();
      else dialog.removeAttribute('open');
    }
  }, [open]);

  if (!open) return null;
  return (
    <dialog
      ref={ref}
      className="confirm-dialog"
      aria-labelledby={titleId}
      onCancel={(e) => {
        e.preventDefault();
        onCancel();
      }}
    >
      <h2 id={titleId}>{title}</h2>
      {body && <p>{body}</p>}
      <div className="confirm-dialog-actions">
        <button type="button" className="teacher-button secondary" onClick={onCancel} disabled={busy}>
          Cancel
        </button>
        <button type="button" className="teacher-button danger" onClick={onConfirm} disabled={busy} autoFocus>
          {busy ? 'Working…' : confirmLabel}
        </button>
      </div>
    </dialog>
  );
}

export default ConfirmDialog;
