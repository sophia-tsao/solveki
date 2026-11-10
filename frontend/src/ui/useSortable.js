import { useState } from 'react';

// Client-side sorting for a table. `columns` maps a column key to a function
// returning that row's sort value (numbers, strings, or null — nulls sort
// last either way). Returns the sorted rows plus props for each header button.
export function useSortable(rows, columns, initial = { key: null, dir: 'asc' }) {
  const [sort, setSort] = useState(initial);

  // Tables here are a class roster at most, so sorting every render is cheap.
  const get = columns[sort.key];
  let sorted = rows;
  if (get) {
    const sign = sort.dir === 'asc' ? 1 : -1;
    sorted = [...rows].sort((a, b) => {
      const va = get(a);
      const vb = get(b);
      if (va == null && vb == null) return 0;
      if (va == null) return 1;
      if (vb == null) return -1;
      if (typeof va === 'string') return sign * va.localeCompare(vb);
      return sign * (va - vb);
    });
  }

  const headerProps = (key) => ({
    type: 'button',
    className: 'teacher-sort',
    'data-dir': sort.key === key ? sort.dir : undefined,
    onClick: () =>
      setSort((s) => (s.key === key ? { key, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'asc' })),
  });

  // For the <th>: announces the active sort to screen readers.
  const ariaSort = (key) => (sort.key === key ? (sort.dir === 'asc' ? 'ascending' : 'descending') : undefined);

  return { rows: sorted, sort, setSort, headerProps, ariaSort };
}
