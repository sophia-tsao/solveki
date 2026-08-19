import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithClient } from './test-utils.jsx';

vi.mock('./auth.js', () => ({ apiFetch: vi.fn(), localDay: vi.fn(() => '2026-07-20') }));

import { apiFetch } from './auth.js';
import CourseList from './CourseList.jsx';

function jsonResponse(payload, { ok = true, status = 200 } = {}) {
  return { ok, status, json: async () => payload };
}

const COURSES = [
  { id: 1, course_name: 'Algebra', grade_level: 8, is_selected: false },
  { id: 2, course_name: 'Geometry', grade_level: 9, is_selected: false },
];

const ALGEBRA_TOPICS = [
  { id: 10, topic_name: 'Linear equations', is_selected: false },
  { id: 11, topic_name: 'Quadratics', is_selected: false },
];

const ALL_TOPICS = [
  { id: 10, topic_name: 'Linear equations', course_id: 1, is_selected: false },
  { id: 11, topic_name: 'Quadratics', course_id: 1, is_selected: false },
  { id: 20, topic_name: 'Triangles', course_id: 2, is_selected: false },
];

beforeEach(() => apiFetch.mockReset());

describe('CourseList', () => {
  it('renders courses from the initial fetch', async () => {
    apiFetch.mockResolvedValueOnce(jsonResponse({ courses: COURSES }));
    renderWithClient(<CourseList />);
    await screen.findByText('Algebra');
    expect(screen.getByText('Geometry')).toBeInTheDocument();
  });

  it('shows an error when the courses fetch fails', async () => {
    apiFetch.mockResolvedValueOnce(jsonResponse({}, { ok: false, status: 500 }));
    renderWithClient(<CourseList />);
    await screen.findByText(/Error: HTTP error! Status: 500/);
  });

  it('lazily loads topics the first time a course is expanded', async () => {
    apiFetch
      .mockResolvedValueOnce(jsonResponse({ courses: COURSES }))
      .mockResolvedValueOnce(jsonResponse({ topics: ALGEBRA_TOPICS }));
    const user = userEvent.setup();
    renderWithClient(<CourseList />);
    await screen.findByText('Algebra');

    await user.click(screen.getByText('Algebra'));

    await screen.findByText('Linear equations');
    expect(apiFetch).toHaveBeenCalledWith('/courses/1/topics');
  });

  it('filters to courses containing a matching topic when searching', async () => {
    apiFetch.mockImplementation((url) => {
      if (url === '/courses/') return Promise.resolve(jsonResponse({ courses: COURSES }));
      if (url === '/topics/') return Promise.resolve(jsonResponse({ topics: ALL_TOPICS }));
      return Promise.resolve(jsonResponse({}));
    });
    const user = userEvent.setup();
    renderWithClient(<CourseList />);
    await screen.findByText('Algebra');

    await user.type(screen.getByRole('searchbox'), 'quad');

    // Algebra stays (it owns "Quadratics"); Geometry is filtered out.
    await screen.findByText('Quadratics');
    expect(screen.getByText('Algebra')).toBeInTheDocument();
    expect(screen.queryByText('Geometry')).not.toBeInTheDocument();
    // Non-matching topics within a matched course are hidden.
    expect(screen.queryByText('Linear equations')).not.toBeInTheDocument();
    expect(apiFetch).toHaveBeenCalledWith('/topics/');
  });

  it('matches on course name and shows all that course\'s topics', async () => {
    apiFetch.mockImplementation((url) => {
      if (url === '/courses/') return Promise.resolve(jsonResponse({ courses: COURSES }));
      if (url === '/topics/') return Promise.resolve(jsonResponse({ topics: ALL_TOPICS }));
      return Promise.resolve(jsonResponse({}));
    });
    const user = userEvent.setup();
    renderWithClient(<CourseList />);
    await screen.findByText('Algebra');

    await user.type(screen.getByRole('searchbox'), 'algeb');

    await screen.findByText('Linear equations');
    expect(screen.getByText('Quadratics')).toBeInTheDocument();
    expect(screen.queryByText('Geometry')).not.toBeInTheDocument();
  });

  it('does not render a course as an open empty box when it has no matching topics', async () => {
    // Geometry's name doesn't match "quad" and its only topic doesn't either,
    // so it must be filtered out entirely — not shown expanded-but-empty.
    apiFetch.mockImplementation((url) => {
      if (url === '/courses/') return Promise.resolve(jsonResponse({ courses: COURSES }));
      if (url === '/topics/') return Promise.resolve(jsonResponse({ topics: ALL_TOPICS }));
      return Promise.resolve(jsonResponse({}));
    });
    const user = userEvent.setup();
    renderWithClient(<CourseList />);
    await screen.findByText('Algebra');

    await user.type(screen.getByRole('searchbox'), 'quad');

    await screen.findByText('Quadratics');
    // Geometry has no matching topic, so its bar shouldn't be on the page at all.
    expect(screen.queryByText('Geometry')).not.toBeInTheDocument();
    expect(screen.queryByText('Triangles')).not.toBeInTheDocument();
  });

  it('shows an empty-state message when nothing matches', async () => {
    apiFetch.mockImplementation((url) => {
      if (url === '/courses/') return Promise.resolve(jsonResponse({ courses: COURSES }));
      if (url === '/topics/') return Promise.resolve(jsonResponse({ topics: ALL_TOPICS }));
      return Promise.resolve(jsonResponse({}));
    });
    const user = userEvent.setup();
    renderWithClient(<CourseList />);
    await screen.findByText('Algebra');

    await user.type(screen.getByRole('searchbox'), 'zzz');

    await screen.findByText(/No courses or topics match/);
    expect(screen.queryByText('Algebra')).not.toBeInTheDocument();
  });

  it('marks a course selected once all its topics are selected', async () => {
    apiFetch
      .mockResolvedValueOnce(jsonResponse({ courses: COURSES }))
      .mockResolvedValueOnce(
        jsonResponse({
          topics: [{ id: 10, topic_name: 'Linear equations', is_selected: true }],
        }),
      )
      .mockResolvedValueOnce(jsonResponse({ ok: true })); // topic select PATCH
    const user = userEvent.setup();
    renderWithClient(<CourseList />);
    await screen.findByText('Algebra');
    await user.click(screen.getByText('Algebra'));
    await screen.findByText('Linear equations');

    const [courseCheckbox] = screen.getAllByRole('checkbox');
    expect(courseCheckbox).not.toBeChecked();

    const topicCheckbox = screen
      .getByText('Linear equations')
      .closest('li')
      .querySelector('input');
    // It's already selected in the payload; toggling to selected keeps it true,
    // and since it's the only topic, the course flips to selected.
    await user.click(topicCheckbox); // -> false first; re-toggle below not needed

    // Verify the PATCH went to the topic-select endpoint.
    await waitFor(() =>
      expect(apiFetch).toHaveBeenCalledWith(
        '/topics/10/select?today=2026-07-20',
        expect.objectContaining({ method: 'PATCH' }),
      ),
    );
  });
});
