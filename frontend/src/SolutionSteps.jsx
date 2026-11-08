import { useState } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { renderMixedLatex } from './mathRender.jsx';
import './SolutionSteps.css';

// A step's equation on its own centered line. Rendered in inline mode with
// \displaystyle rather than KaTeX's display mode: it looks the same, but inline
// math can wrap after = or +, so a long line breaks instead of overflowing the
// card (which would give it a scrollbar).
function DisplayMath({ math }) {
  const html = katex.renderToString(`\\displaystyle ${math}`, { throwOnError: false });
  return <div className="solution-step-math" dangerouslySetInnerHTML={{ __html: html }} />;
}

// The worked solution shown on a card's incorrect face once both attempts are
// used up. Collapsed behind a toggle so the answer and the Continue/Report
// actions stay in view; renders nothing for problems without an explanation.
// Each step is `{ text, math }`: a sentence with inline `$...$` LaTeX, plus an
// optional display-math line (see backend generators/_steps.py).
export default function SolutionSteps({ steps }) {
  const [open, setOpen] = useState(false);
  if (!steps?.length) return null;
  return (
    <div className="solution-steps">
      <button
        type="button"
        className="solution-steps-toggle"
        aria-expanded={open}
        onClick={() => setOpen(o => !o)}
      >
        {open ? 'Hide step-by-step solution' : 'See step-by-step solution'}
      </button>
      {open && (
        <ol className="solution-steps-list">
          {steps.map((step, i) => (
            <li key={i} className="solution-step">
              <span className="solution-step-text">{renderMixedLatex(step.text)}</span>
              {step.math && <DisplayMath math={step.math} />}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
