import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Header from './Header.jsx';
import { parseHash, hashFor } from './router.js';

describe('Header', () => {
  it('marks the current page button as active', () => {
    render(<Header currentPage="settings" linkClicked={() => {}} />);
    expect(screen.getByRole('button', { name: 'Settings' })).toHaveClass('active');
    expect(screen.getByRole('button', { name: 'Practice' })).not.toHaveClass('active');
  });

  it('calls linkClicked with the target page key', async () => {
    const linkClicked = vi.fn();
    const user = userEvent.setup();
    render(<Header currentPage="math" linkClicked={linkClicked} />);
    await user.click(screen.getByRole('button', { name: 'Available Courses' }));
    expect(linkClicked).toHaveBeenCalledWith('courses');
  });

  it('navigates to the dashboard', async () => {
    const linkClicked = vi.fn();
    const user = userEvent.setup();
    render(<Header currentPage="math" linkClicked={linkClicked} />);
    await user.click(screen.getByRole('button', { name: 'Dashboard' }));
    expect(linkClicked).toHaveBeenCalledWith('dashboard');
  });

  it('gives teachers three areas, with the guide and settings to the side', async () => {
    const linkClicked = vi.fn();
    const user = userEvent.setup();
    render(<Header role="teacher" user={{ name: 'Sophia Tsao' }} currentPage="teacher-overview" linkClicked={linkClicked} />);
    const nav = screen.getByRole('navigation');
    expect(Array.from(nav.querySelectorAll('button')).map((b) => b.textContent))
      .toEqual(['Home', 'Classes', 'Assignments']);
    await user.click(screen.getByRole('button', { name: 'Guide' }));
    expect(linkClicked).toHaveBeenCalledWith('teacher-guide');
    await user.click(screen.getByRole('button', { name: 'Account' }));
    await user.click(screen.getByRole('menuitem', { name: 'Settings' }));
    expect(linkClicked).toHaveBeenCalledWith('settings');
    expect(screen.getByRole('button', { name: 'Account' })).toHaveTextContent('ST');
  });

  it('lights up the parent area on detail pages', () => {
    render(<Header role="teacher" currentPage="student-detail" linkClicked={() => {}} />);
    expect(screen.getByRole('button', { name: 'Classes' })).toHaveClass('active');
    expect(screen.getByRole('button', { name: 'Home' })).not.toHaveClass('active');
  });
});

describe('router', () => {
  it('parses a page, an id and query params', () => {
    expect(parseHash('#/student-detail/41?class=3')).toEqual({ page: 'student-detail', id: 41, params: { class: '3' } });
    expect(parseHash('#/classes')).toEqual({ page: 'classes', id: null, params: {} });
  });

  it('builds the hash back, dropping empty params', () => {
    expect(hashFor({ page: 'class-detail', id: 3, params: { tab: 'progress', x: '' } })).toBe('#/class-detail/3?tab=progress');
    expect(hashFor({ page: 'classes' })).toBe('#/classes');
  });
});
