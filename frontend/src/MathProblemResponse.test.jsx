import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MathProblemResponse from './MathProblemResponse.jsx';

// `verdict` is what the (backend-backed) onSubmit resolves to.
function setup(verdict = true) {
  const onSubmit = vi.fn(async () => verdict);
  render(<MathProblemResponse resetKey="1" onSubmit={onSubmit} />);
  return { onSubmit, user: userEvent.setup() };
}

describe('MathProblemResponse', () => {
  it('hands the typed answer to onSubmit for grading', async () => {
    const { onSubmit, user } = setup();
    await user.type(screen.getByRole('textbox'), '42');
    await user.click(screen.getByRole('button'));
    expect(onSubmit).toHaveBeenCalledWith('42');
  });

  it('shows feedback for a wrong answer', async () => {
    const { user } = setup(false);
    await user.type(screen.getByRole('textbox'), '7');
    await user.click(screen.getByRole('button'));
    expect(await screen.findByRole('button')).toHaveTextContent('Incorrect!');
  });

  it('submits on Enter', async () => {
    const { onSubmit, user } = setup();
    await user.type(screen.getByRole('textbox'), '42{Enter}');
    expect(onSubmit).toHaveBeenCalledWith('42');
  });

  it('clears the input after a verdict', async () => {
    const { user } = setup(false);
    const input = screen.getByRole('textbox');
    await user.type(input, '7');
    await user.click(screen.getByRole('button'));
    expect(input).toHaveValue('');
  });

  it('keeps the answer when there is no verdict (e.g. a failed check)', async () => {
    const { user } = setup(null);
    const input = screen.getByRole('textbox');
    await user.type(input, '7');
    await user.click(screen.getByRole('button'));
    expect(input).toHaveValue('7');
    expect(screen.getByRole('button')).toHaveTextContent('Submit');
  });

  it('disables Submit while a check is in flight', async () => {
    let resolve;
    const onSubmit = vi.fn(() => new Promise((r) => { resolve = r; }));
    render(<MathProblemResponse resetKey="1" onSubmit={onSubmit} />);
    const user = userEvent.setup();
    await user.type(screen.getByRole('textbox'), '42');
    await user.click(screen.getByRole('button'));
    expect(screen.getByRole('button')).toBeDisabled();
    await user.type(screen.getByRole('textbox'), '{Enter}');
    expect(onSubmit).toHaveBeenCalledTimes(1);
    resolve(true);
  });

  it('ignores a blank submission', async () => {
    const { onSubmit, user } = setup();
    await user.click(screen.getByRole('button'));
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole('button')).toHaveTextContent('Submit');
  });

  it('ignores a whitespace-only submission', async () => {
    const { onSubmit, user } = setup();
    await user.type(screen.getByRole('textbox'), '   ');
    await user.click(screen.getByRole('button'));
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
