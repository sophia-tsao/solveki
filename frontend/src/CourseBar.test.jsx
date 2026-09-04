import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CourseBar from './CourseBar.jsx';

const TOPICS = [
  { id: 1, topic_name: 'Addition', selection_status: 'selected' },
  { id: 2, topic_name: 'Subtraction', selection_status: 'unselected' },
];

function setup(overrides = {}) {
  const props = {
    id: 7,
    courseName: 'Algebra',
    gradeLevel: 8,
    topics: TOPICS,
    isOpen: false,
    courseSelection: 'none',
    onItemClick: vi.fn(),
    onTopicToggle: vi.fn(),
    onCourseToggle: vi.fn(),
    ...overrides,
  };
  render(<CourseBar {...props} />);
  return { props, user: userEvent.setup() };
}

describe('CourseBar', () => {
  it('renders the course name and grade', () => {
    setup();
    expect(screen.getByText('Algebra')).toBeInTheDocument();
    expect(screen.getByText('Grade 8')).toBeInTheDocument();
  });

  it('fires onItemClick with the course id when the bar is clicked', async () => {
    const { props, user } = setup();
    await user.click(screen.getByText('Algebra'));
    expect(props.onItemClick).toHaveBeenCalledWith(7);
  });

  it('toggles the course without also firing the bar click (stopPropagation)', async () => {
    const { props, user } = setup();
    // The course checkbox is the first checkbox in the header.
    const [courseCheckbox] = screen.getAllByRole('checkbox');
    await user.click(courseCheckbox);
    expect(props.onCourseToggle).toHaveBeenCalledWith(7, true);
    expect(props.onItemClick).not.toHaveBeenCalled();
  });

  it('toggles an individual topic with its id and new value', async () => {
    const { props, user } = setup();
    // "Subtraction" is currently unselected -> clicking selects it.
    const subtractionCheckbox = screen
      .getByText('Subtraction')
      .closest('li')
      .querySelector('input');
    await user.click(subtractionCheckbox);
    expect(props.onTopicToggle).toHaveBeenCalledWith(7, 2, true);
    expect(props.onItemClick).not.toHaveBeenCalled();
  });

  it('reflects the course-selected checkbox state', () => {
    setup({ courseSelection: 'all' });
    const [courseCheckbox] = screen.getAllByRole('checkbox');
    expect(courseCheckbox).toBeChecked();
  });

  it('shows the indeterminate dash when the course is partially selected', () => {
    setup({ courseSelection: 'partial' });
    const [courseCheckbox] = screen.getAllByRole('checkbox');
    expect(courseCheckbox).not.toBeChecked();
    expect(courseCheckbox.indeterminate).toBe(true);
  });

  it('groups topics under their unit title, preserving order', () => {
    setup({
      topics: [
        { id: 1, topic_name: 'Addition', selection_status: 'unselected', unit_key: 'u1', unit_name: 'Number Sense' },
        { id: 2, topic_name: 'Subtraction', selection_status: 'unselected', unit_key: 'u1', unit_name: 'Number Sense' },
        { id: 3, topic_name: 'Solving Equations', selection_status: 'unselected', unit_key: 'u2', unit_name: 'Algebra Basics' },
      ],
    });
    const titles = screen.getAllByRole('heading', { level: 3 }).map((h) => h.textContent);
    expect(titles).toEqual(['Number Sense', 'Algebra Basics']);
    // Two topics live under the first unit heading, one under the second.
    const units = document.querySelectorAll('.course-bar-unit');
    expect(units[0].querySelectorAll('li')).toHaveLength(2);
    expect(units[1].querySelectorAll('li')).toHaveLength(1);
  });
});
