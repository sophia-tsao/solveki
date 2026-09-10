import katex from 'katex';
import 'katex/dist/katex.min.css';

// Render an inline LaTeX fragment. Shared by the practice deck and the
// assignment player so both format problems identically.
export function InlineMath({ math }) {
  const html = katex.renderToString(math, { throwOnError: false });
  return <span dangerouslySetInnerHTML={{ __html: html }} />;
}

// Split a string on '$' delimiters, rendering the odd segments as inline math.
export function renderMixedLatex(str) {
  if (!str) return null;
  return str.split('$').map((segment, i) =>
    i % 2 === 1 ? <InlineMath key={i} math={segment} /> : segment
  );
}
