import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import MathProblemDisplay from './MathProblemDisplay.jsx';

describe('MathProblemDisplay', () => {
  it('renders the problem it is given inside the display wrapper', () => {
    const { container } = render(<MathProblemDisplay problem="What is 2+2?" />);
    expect(screen.getByText('What is 2+2?')).toBeInTheDocument();
    expect(container.querySelector('.math-problem-display')).toBeInTheDocument();
  });

  it('renders rich problem content (e.g. a prerendered node)', () => {
    render(<MathProblemDisplay problem={<span data-testid="katex">x^2</span>} />);
    expect(screen.getByTestId('katex')).toHaveTextContent('x^2');
  });
});
