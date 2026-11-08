import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Echo the LaTeX source (tagged with the mode) so tests can see what was rendered.
vi.mock('katex', () => ({
  default: {
    renderToString: (math, opts) => `${opts?.displayMode ? 'display' : 'inline'}:${math}`,
  },
}));

import SolutionSteps from './SolutionSteps.jsx';

const STEPS = [
  { text: 'Subtract $3$ from both sides.', math: '2x = 4' },
  { text: 'Divide both sides by $2$.', math: null },
];

describe('SolutionSteps', () => {
  it('renders nothing without steps', () => {
    const { container } = render(<SolutionSteps steps={[]} />);
    expect(container).toBeEmptyDOMElement();
    const { container: missing } = render(<SolutionSteps />);
    expect(missing).toBeEmptyDOMElement();
  });

  it('starts collapsed and expands into numbered steps', async () => {
    const user = userEvent.setup();
    render(<SolutionSteps steps={STEPS} />);
    const toggle = screen.getByRole('button', { name: 'See step-by-step solution' });
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByRole('list')).not.toBeInTheDocument();

    await user.click(toggle);
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
    expect(toggle).toHaveTextContent('Hide step-by-step solution');
    const items = screen.getAllByRole('listitem');
    expect(items).toHaveLength(2);
    // Inline math in the sentence, plus the step's equation line. That line is
    // inline-mode \displaystyle (it can wrap), never KaTeX display mode.
    expect(items[0]).toHaveTextContent(String.raw`Subtract inline:3 from both sides.inline:\displaystyle 2x = 4`);
    expect(items[1]).toHaveTextContent('Divide both sides by inline:2.');
    expect(items[1]).not.toHaveTextContent('displaystyle');
    expect(screen.getByRole('list')).not.toHaveTextContent('display:');

    await user.click(toggle);
    expect(screen.queryByRole('list')).not.toBeInTheDocument();
  });
});
